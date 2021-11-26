import typing

from .YamlFieldChecker      import YamlFieldChecker, YamlFieldCheckResult
from .YamlDependencyChecker import YamlDependencyChecker, YamlDependencyCheckerResult
from .CppFieldGenerator     import CppFieldGenerator, ByteToTypeConverter
from .CppTypesGenerator     import CppTypesGenerator



class CppClassDeclarationGenerator():
    """ 
    Takes a 'dict' defining class fields/members, user defined types/enums
    and generates a C++ class declaration header. The generated classes all 
    inherit from ICatbuffer. 
    
    A C++ generated file can be written by calling 'write_file()'.
    """

    def init( self, 
              class_name:  str,
              fields:      dict,
              user_types:  CppTypesGenerator,
              class_decls: typing.Dict[str, "CppClassDeclarationGenerator"],
              comment:     str = ""
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
                
        self.conditions : typing.Dict[str, list]                    = {}                      # Stores a list of condition fields
                
        self.__name_to_enum                                         = user_types.name_to_enum # Dict of all enums
        self.__name_to_type                                         = user_types.name_to_type # Dict of all user defined types
        self.__name_to_class                                        = class_decls
                    
        self.__lib_includes : typing.Set[str]                       = set()                   # Set of all C++ library includes
        self.__includes : typing.Set[str]                           = set()                   # Set of all normal includes
                
        self.__include_code_output                                  = ""                      # Generated C++ include code goes here
        self.__header_code_output                                   = ""                      # Generated C++ class declaration code goes here
                    
        self.__dependency_checks : typing.List[dict]                = list()

        result, result_str = self.__find_condition_fields()
        if result != YamlFieldCheckResult.OK:
            return result, result_str

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

            if "array sized" == disposition:
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
        self.__header_code_output += 'public:\n'

        for idx, field in enumerate(self.fields):
            name     = field["name"]     if "name"     in field else ""
            size     = field["size"]     if "size"     in field else 0
            comments = field["comments"] if "comments" in field else ""

            result, result_str = YamlFieldChecker.check_type(self.class_name, field)
            if result != YamlFieldCheckResult.OK:
                return result, result_str

            if( "disposition" in field ):
                disposition = field["disposition"]

                #TODO: refactor this when disposition is removed
                field_type = ByteToTypeConverter.get_disposition_type( field ) 
                field["type"] = field_type  

                if( "const" == disposition ):
                    # check fields
                    result, result_str = YamlFieldChecker.const(self.class_name, field, self.__name_to_enum)
                    if YamlFieldCheckResult.OK != result:
                        return result, result_str

                    # check if const defines a class type/version 
                    """
                    NOTE:
                    If const defines a transaction type, it is saved for later. Will be used for generating type_to_class_xyz() functions later.
                    This is a hack because the schemas don't yet support assigning an enum type as a class/transaction type yet!
                    For now each class must have a const field named "TRANSACTION_TYPE" that defines the class type.
                    """
                    if "TRANSACTION_TYPE" == field["name"]:
                        self.group_type = field_type
                        self.group_id   = field["value"]
                    elif "TRANSACTION_VERSION" == field["name"]:
                        self.group_version = field["value"]

                    #generate
                    self.__header_code_output += CppFieldGenerator.gen_const_field( field_type, name, field["value"], comments )

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
                    self.__header_code_output += CppFieldGenerator.gen_reserved_field( field_type, name, size, comments )

                elif( "array" == disposition ):
                    # check fields
                    result, result_str = YamlFieldChecker.array(self.class_name, field, idx, self.member_vars)
                    if YamlFieldCheckResult.OK != result:
                        return result, result_str

                    # generate
                    self.__header_code_output += CppFieldGenerator.gen_array_field( field_type, name, comments )
                    self.__lib_includes.add("#include <vector>")

                elif( "array sized" == disposition ):
                    # check fields
                    result, result_str = YamlFieldChecker.array_sized(self.class_name, field)
                    if YamlFieldCheckResult.OK != result:
                        return result, result_str

                    # add to list of dependency checks
                    self.__dependency_checks.append(field) # check again later when all classes are declared

                    # generate
                    self.__header_code_output += CppFieldGenerator.gen_array_sized_field( name, comments )
                    self.__lib_includes.add("#include <vector>")
                    self.__lib_includes.add("#include <memory>")

                elif( "array fill" == disposition ):
                    # check fields
                    result, result_str = YamlFieldChecker.array_fill(self.class_name, field, self.__name_to_class)
                    if YamlFieldCheckResult.OK != result:
                        return result, result_str

                    # generate
                    self.__header_code_output += CppFieldGenerator.gen_array_fill_field( field_type, name, comments )
                    self.__lib_includes.add("#include <vector>")

                else:
                    return YamlFieldCheckResult.DISPOSITION_INVALID, f"\n\nERROR: Invalid disposition '{disposition}' in struct '{self.class_name}'!\n\n"

            else:
                field_type = ByteToTypeConverter.get_field_type( field )
                field["type"] = field_type

                if field_type not in CppFieldGenerator.builtin_types and \
                   field_type not in self.__name_to_enum and \
                   field_type not in self.__name_to_type and \
                   field_type not in self.__name_to_class:
                    return YamlFieldCheckResult.TYPE_UNKNOWN, f"\n\nError: Type '{field_type}' in struct '{self.class_name}' not defined'!\n\n"

                if "condition" in field: # generate condition field
                    cond_var = field["condition"]

                    # check cond var has been defined #TODO: Disabled for now. Enable when adding Enums
#                    if cond_var not in self.member_vars:
#                        return DeclGenResult.CONDITION_VAR_NOT_DEFINED, f"\n\nError: Condition variable '{cond_var}' not defined in struct '{self.class_name}'!\n\n"
                    #self.__consistency_checks.append(field) # check again later when all classes are declared

                    if cond_var in conditions:
                        self.__header_code_output += CppFieldGenerator.gen_condition_field( cond_var, conditions[cond_var] )
                        self.__lib_includes.add("#include <vector>")
                        del conditions[cond_var]
                        
                else: # generate normal field
                    # check name exists
                    if not name:
                        return YamlFieldCheckResult.NAME_MISSING, "\n\nError: Missing 'name' key for field in struct '{self.class_name}'!\n\n"
                    self.__header_code_output += CppFieldGenerator.gen_normal_field( field_type, name, size, comments )

                    # check name not declared yet
                    if name in self.member_vars:
                        return YamlFieldCheckResult.NAME_REDEFINED, f"\n\nError: Same field name '{name}' declared multiple times in struct '{self.class_name}'!\n\n"

                    # save
                    self.member_vars[name] = (idx, field_type)


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

        for include in self.__includes:
            self.__include_code_output += (include + "\n")

        self.__include_code_output += '\n'



inherited_methods = """\t
\t// ICatbuffer inherited methods
\tbool   Deserialize( RawBuffer& buffer ) override;
\tbool   Serialize  ( RawBuffer& buffer ) override;
\tsize_t Size       (                   ) override;\n\n\n"""
