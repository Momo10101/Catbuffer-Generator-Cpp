import typing

from .CppFieldGenerator import CppFieldGenerator, ByteToTypeConverter
from .CppTypesGenerator import CppTypesGenerator



class CppClassDeclarationGenerator():
    """ 
    Takes a 'dict' defining class fields/members, user defined types/enums
    and generates a C++ class declaration header. The generated classes all 
    inherit from ICatbuffer. 
    
    A C++ generated file can be written by calling 'write_file()'.
    """


    def __init__( self, class_name: str, fields: dict, types: CppTypesGenerator,
                  comment: str = "" ):
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
        """

        self.class_name                          = class_name
        self.fields                              = fields
        self.comment                             = comment
                
        self.group_type                          = ""                 # The enum group that the class belongs to (if any)
        self.group_id                            = ""                 # The id of the class, within the above group
                
        self.conditions : typing.Dict[str, list] = {}                 # Stores a list of condition fields

        self.__name_to_enum                      = types.name_to_enum # Dict of all enums
        self.__name_to_type                      = types.name_to_type # Dict of all user defined types
    
        self.__lib_includes : typing.Set[str]    = set()              # Set of all C++ library includes
        self.__includes : typing.Set[str]        = set()              # Set of all normal includes

        self.__include_code_output               = ""                 # Generated C++ include code goes here
        self.__header_code_output                = ""                 # Generated C++ class declaration code goes here
                    

        self.__find_condition_fields()
        self.__generate_header()



    def write_file( self, file_path: str ) -> None:
        self.__generate_includes()

        f = open( file_path, "w" )
        f.write(self.__include_code_output)
        f.write(self.__header_code_output)



    def __find_condition_fields( self ):
        """
        Finds condition fields and stores them in 'self.conditions'.
        Fields which share the same condition are grouped together 
        in the same list. Needed for doing coinditions and unions 
        later.
        """

        for field in self.fields:

            # skip if not condition
            if( "condition" not in field ):
                continue
            
            # save field
            if field["condition"] not in self.conditions:
                self.conditions[ field["condition"] ] = []
            self.conditions[ field["condition"] ].append( field )

            # add include if type is a class
            type = field[ "type" ]
            if type not in self.__name_to_enum and type not in self.__name_to_type and type not in CppFieldGenerator.builtin_types:
                self.__include_code_output += f'#include "{type}.h"\n'



    def __generate_header( self ):
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

        for field in self.fields:
            name     = field["name"]     if "name"     in field else ""
            size     = field["size"]     if "size"     in field else 0
            comments = field["comments"] if "comments" in field else ""

            if( "disposition" in field ):
                disposition = field["disposition"]
                
                type = ByteToTypeConverter.get_disposition_type( field )
                field["type"] = type #TODO: dont do this perhaps? 

                if( "const" == disposition ):
                    """
                    NOTE:
                    If const defines a transaction type, it is saved for later. Will be used for generating type_to_class_xyz() functions later.
                    This is a hack because the schemas dont yet support assigning an enum type as a class/transaction type yet!
                    For now each class must have a const field named "TRANSACTION_TYPE" that defines the class type.
                    """
                    if "TRANSACTION_TYPE" == field["name"]:
                        self.group_type = type
                        self.group_id   = field["value"]

                    self.__header_code_output += CppFieldGenerator.gen_const_field( type, name, field["value"], comments )

                elif( "inline" == disposition ):
                    self.__header_code_output += CppFieldGenerator.gen_inline_field( type, comments )

                elif( "reserved" == disposition ):
                    self.__header_code_output += CppFieldGenerator.gen_reserved_field( type, name, size, comments )

                elif( "array" == disposition ):
                    self.__header_code_output += CppFieldGenerator.gen_array_field( type, name, comments )
                    self.__lib_includes.add("#include <vector>")

                elif( "array sized" == disposition ):
                    self.__header_code_output += CppFieldGenerator.gen_array_sized_field( name, comments )
                    self.__lib_includes.add("#include <vector>")
                    self.__lib_includes.add("#include <memory>")

                elif( "array fill" == disposition ):
                    self.__header_code_output += CppFieldGenerator.gen_array_fill_field( type, name, comments )
                    self.__lib_includes.add("#include <vector>")

                else:
                    print( "ERROR: disposition not known: ", disposition )
                    exit(1)

            else:
                type = ByteToTypeConverter.get_field_type( field )
                field["type"] = type

                if "condition" in field: # generate condition field
                    cond = field["condition"]
                    if cond in conditions:
                        self.__header_code_output += CppFieldGenerator.gen_condition_field( cond, conditions[cond] )
                        self.__lib_includes.add("#include <vector>")
                        del conditions[cond]
                        
                else: # generate normal field
                    self.__header_code_output += CppFieldGenerator.gen_normal_field( type, name, size, comments )


            # Add include
            if type not in self.__name_to_enum and type not in self.__name_to_type and type not in CppFieldGenerator.builtin_types:
                self.__includes.add(f'#include "{type}.h"')

        self.__header_code_output += "\n};"



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
