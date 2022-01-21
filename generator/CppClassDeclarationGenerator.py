import typing

from .YamlFieldChecker      import YamlFieldChecker, YamlFieldCheckResult
from .YamlDependencyChecker import YamlDependencyChecker, YamlDependencyCheckerResult
from .CppFieldGenerator     import CppFieldGenerator, TypeConverter
from .CppTypesGenerator     import CppTypesGenerator



class CppClassDeclarationGenerator():
    """ 
    Takes a 'dict' defining class fields/members, user defined types/enums
    and generates a C++ class declaration header. The generated classes all 
    inherit from ICatbuffer. 
    
    A C++ generated file can be written by calling 'write_file()'.
    """

    def init( self, 
              class_name:      str,
              fields:          dict,
              user_types:      CppTypesGenerator,
              class_decls:     typing.Dict[str, "CppClassDeclarationGenerator"],
              comment:         str = "",
              prettyprinter:   bool = False
              ) -> typing.Tuple[YamlFieldCheckResult, str]:
        """
        Parameters
        ----------
        class_name : str
            The name of the class which will be used for the header
            class declaration.

        field : dict
            The class member fields

        types : CppTypesGenerator
            The generator which was used to process user defined types.

        comment : str, optional
            Description of the class which will be used as a doxygen
            comment.

        prettyprinter: bool, optional
            Set to true for pretty printing functionality

        returns : bool
            True if class correctly initialized using input parameters
        """

        self.class_name                                             = class_name
        self.fields                                                 = fields
        self.comment                                                = comment
        self.member_vars : typing.Dict[str, typing.Tuple[int, str]] = {}                      # Dict to store variable name to type

        self.group_type                                             = ""                      # The enum group that the class belongs to (if any)
        self.group_id                                               = ""                      # The id of the class, within the above group
        self.group_version                                          = ""                      # The version of the group
        self.group_header                                           = ""

        self.header_version_field                                   = ""
        self.header_type_field                                      = ""

        self.conditions : typing.Dict[str, list]                    = {}                      # Stores a list of condition fields
        self.size_to_arrays : typing.Dict[str, typing.List[str]]    = {}                      # For each variable used as an array size, stores the list of arrays which depend on that variable 

        self.__name_to_enum                                         = user_types.name_to_enum # Dict of all enums
        self.__name_to_alias                                        = user_types.name_to_alias # Dict of all user defined types
        self.__name_to_class                                        = class_decls
                    
        self.__lib_includes : typing.Set[str]                       = set()                   # Set of all C++ library includes
        self.__includes : typing.Set[str]                           = set()                   # Set of all normal includes
                
        self.__include_code_output                                  = ""                      # Generated C++ include code goes here
        self.__header_code_output                                   = ""                      # Generated C++ class declaration code goes here
                    
        self.__dependency_checks : typing.List[dict]                = list()

        self.__prettyprinter                                        = prettyprinter

        result, result_str = self.__find_condition_fields()
        if result != YamlFieldCheckResult.OK:
            return result, result_str

        #TODO: Disabled for now due to incompatibility with NEM conditional arrays, enable later on.
        #      Perhaps add command line option for generating size fields or not.
        #self.__find_array_size_fields() 

        return self.__generate_header()



    def write_file( self, file_path: str ) -> None:
        self.__generate_includes()

        f = open( file_path, "w" )
        f.write(self.__include_code_output)
        f.write(self.__header_code_output)


    # should be called when all structs/classes have been processed.
    def check_dependency(self) -> typing.Tuple["YamlDependencyCheckerResult", str]:
        
        for field in self.__dependency_checks:
            disposition = field["disposition"]

            if "array_sized" == disposition:
                result, result_str = YamlDependencyChecker.array_sized( self.class_name, field, self.__name_to_class )
                if YamlDependencyCheckerResult.OK != result:
                    return result, result_str

        return YamlDependencyCheckerResult.OK, ""


    def __find_condition_fields( self ):
        """
        Finds condition fields and stores them in 'self.conditions'.
        Fields which share the same condition are grouped together 
        in the same list. Needed for doing conditions and unions 
        later.
        """

        for field in self.fields:

            # skip if not condition
            if( "condition" not in field ):
                continue
            
            result, result_str = YamlFieldChecker.condition(self.class_name, field)
            if YamlFieldCheckResult.OK != result:
                return result, result_str

            # save field
            cond_name = field["condition"]
            if cond_name not in self.conditions:
                self.conditions[ cond_name ] = []

           
            self.conditions[ cond_name ].append( field )

            # add include if type is a class
            type = field[ "type" ]
            if type in self.__name_to_class:               
                self.__include_code_output += f'#include "{type}.h"\n'

        return YamlFieldCheckResult.OK, ""


    def __find_array_size_fields( self ):
        """
        Finds fields that store array sizes and creates the dictionary 
        'array size field' -> list of array names (since a variable can be 
        used as array size for multiple arrays). This is used for not 
        creating a size variable, since it is not needed due to C++ vectors 
        having a size field.
        """

        for field in self.fields:

            if "type" not in field:
                continue

            type = field["type"].split()
            if "array" != type[0]:
                continue

            if( "size" not in field or "name" not in field ):
                continue

            size_var   = field["size"]
            array_name = field["name"]

            if size_var not in self.size_to_arrays:
                self.size_to_arrays[ size_var ] = []

            self.size_to_arrays[ size_var ].append( array_name )


    def __generate_header( self ) -> bool:
        """ 
        Goes through fields of types: 'const', 'inline', 'reserved', 
        'array', 'array sized', 'array fill' and 'condition' and 
        generates corresponding C++ class member declarations.

        Generated class declaration inherits from 'ICatBuffer' 
        and inherited methods are added as 'override'.
        """

        conditions = self.conditions.copy()

        self.__header_code_output  = f'\n\nclass {self.class_name} : public ICatbuffer\n{{\npublic:\n' # class definition
        self.__header_code_output += f'\t{self.class_name}(){{ }};\n'      # constructor
        self.__header_code_output += f'\t~{self.class_name}(){{ }};\n\n\n' # destructor
        self.__header_code_output += inherited_methods

        if self.__prettyprinter:
            self.__header_code_output += "\tvoid   Print      ( const size_t level ) override;\n"

        self.__header_code_output += '\n\npublic:\n'

        for idx, field in enumerate(self.fields):
            comments = field["comments"] if "comments" in field else ""

            result, result_str = YamlFieldChecker.check_type(self.class_name, field)
            if result != YamlFieldCheckResult.OK:
                return result, result_str

            types = field["type"].split()
            
            if len(types) > 1:
                field["disposition"] = types[0]
                field_type           = TypeConverter.convert(types[1])
            else:
                field_type  = TypeConverter.convert(types[0])

            field["type"] = field_type

            if field_type not in CppFieldGenerator.builtin_types and \
               field_type not in self.__name_to_enum and \
               field_type not in self.__name_to_alias and \
               field_type not in self.__name_to_class:
                return YamlFieldCheckResult.TYPE_UNKNOWN, f"\n\nError: Type '{field_type}' in struct '{self.class_name}' not defined or incomplete!\n\n"
                
            if "disposition" in field:

                disposition = field["disposition"]
                if( "const" == disposition ):
                    # check fields
                    result, result_str = YamlFieldChecker.const( self.class_name, field, self.__name_to_enum )
                    if YamlFieldCheckResult.OK != result:
                        return result, result_str

                    #generate
                    self.__header_code_output += CppFieldGenerator.gen_const_field( field_type, field["name"], field["value"], comments )

                elif( "struct_type" == disposition ):
                    self.group_type    = field_type
                    self.group_id      = field["value"].split()[0]
                    self.group_version = field["value"].split()[1][1:]
                    self.group_header  = field["header"]

                    self.header_type_field    = field["type_field"]
                    self.header_version_field = field["version_field"] if "version_field" in field else "" 

                    self.__header_code_output += CppFieldGenerator.gen_const_field( field_type, "TRANSACTION_TYPE",    self.group_id,      comments )
                    self.__header_code_output += CppFieldGenerator.gen_const_field( "uint8_t", "TRANSACTION_VERSION", self.group_version, comments )

                elif( "inline" == disposition ):
                    # check fields
                    result, result_str = YamlFieldChecker.inline(self.class_name, field, self.__name_to_class)
                    if YamlFieldCheckResult.OK != result:
                        return result, result_str

                    # generate 
                    self.__header_code_output += CppFieldGenerator.gen_inline_field( field_type, comments )

                elif( "reserved" == disposition ):
                    # check fields
                    result, result_str = YamlFieldChecker.reserved(self.class_name, field)
                    if YamlFieldCheckResult.OK != result:
                        return result, result_str

                    # generate
                    #self.__header_code_output += CppFieldGenerator.gen_reserved_field( field_type, field["name"], field["size"], comments )

                elif( "array" == disposition ):
                    # check fields
                    result, result_str = YamlFieldChecker.array(self.class_name, field, idx, self.member_vars)
                    if YamlFieldCheckResult.OK != result:
                        return result, result_str

                    # generate
                    self.__header_code_output += CppFieldGenerator.gen_array_field( field_type, field["name"], comments )
                    self.__lib_includes.add("#include <vector>")

                elif( "array_sized" == disposition ):
                    # check fields
                    result, result_str = YamlFieldChecker.array_sized(self.class_name, field)
                    if YamlFieldCheckResult.OK != result:
                        return result, result_str

                    # add to list of dependency checks
                    self.__dependency_checks.append(field) # check again later when all classes are declared

                    # generate
                    self.__header_code_output += CppFieldGenerator.gen_array_sized_field( field["name"], comments )
                    self.__lib_includes.add("#include <vector>")
                    self.__lib_includes.add("#include <memory>")

                elif( "array_fill" == disposition ):
                    # check fields
                    result, result_str = YamlFieldChecker.array_fill(self.class_name, field, self.__name_to_class)
                    if YamlFieldCheckResult.OK != result:
                        return result, result_str

                    # generate
                    self.__header_code_output += CppFieldGenerator.gen_array_fill_field( field_type, field["name"], comments )
                    self.__lib_includes.add("#include <vector>")

                else:
                    return YamlFieldCheckResult.DISPOSITION_INVALID, f"\n\nERROR: Invalid disposition '{disposition}' in struct '{self.class_name}'!\n\n"

            else:
                if "condition" in field: # generate condition field
                    cond_var = field["condition"]

                    # check cond var has been defined #TODO: Disabled for now. Enable when adding Enums
#                    if cond_var not in self.member_vars:
#                        return DeclGenResult.CONDITION_VAR_NOT_DEFINED, f"\n\nError: Condition variable '{cond_var}' not defined in struct '{self.class_name}'!\n\n"
                    #self.__consistency_checks.append(field) # check again later when all classes are declared

                    if cond_var in conditions:
                        self.__header_code_output += CppFieldGenerator.gen_condition_field( cond_var, conditions[cond_var], self.member_vars )
                        self.__lib_includes.add("#include <vector>")
                        del conditions[cond_var]
                        
                else: # generate normal field
                    name = field["name"] if "name" in field else ""
                    size = field["size"] if "size" in field else 0

                    # check name exists
                    if not name:
                        return YamlFieldCheckResult.NAME_MISSING, "\n\nError: Missing 'name' key for field in struct '{self.class_name}'!\n\n"

                    # check name not declared yet
                    if name in self.member_vars:
                        return YamlFieldCheckResult.NAME_REDEFINED, f"\n\nError: Same field name '{name}' declared multiple times in struct '{self.class_name}'!\n\n"


                    # dont generate field if var is the size of an array (in that case the vector 'size()' variable is used instead)
                    if name in self.size_to_arrays:
                        continue

                    # generate code
                    self.__header_code_output += CppFieldGenerator.gen_normal_field( field_type, name, size, comments )


            # save as member var
            if "name" in field:
                self.member_vars[field["name"]] = (idx, field_type)


            # Add include
            if field_type in self.__name_to_class:
                self.__includes.add(f'#include "{field_type}.h"')

        self.__header_code_output += "\n};"
    
        return YamlFieldCheckResult.OK, ""



    def __generate_includes( self ):

        self.__include_code_output = f'#pragma once\n'

        for include in self.__lib_includes:
            self.__include_code_output += (include + "\n")

        self.__include_code_output += '\n'
        self.__include_code_output += '#include "types.h"\n'
        self.__include_code_output += '#include "ICatbuffer.h"\n\n'

        if self.__prettyprinter:
            self.__include_code_output += '#include "IPrettyPrinter.h"\n\n'


        for include in self.__includes:
            self.__include_code_output += (include + "\n")

        self.__include_code_output += '\n'



inherited_methods = """\t
\t// ICatbuffer inherited methods
\tbool   Deserialize( RawBuffer& buffer  ) override;
\tbool   Serialize  ( RawBuffer& buffer  ) override;
\tsize_t Size       (                    ) override;\n"""
