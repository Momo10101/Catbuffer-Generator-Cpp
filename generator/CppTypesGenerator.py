import typing
from dataclasses import dataclass

from .CppFieldGenerator import ByteToTypeConverter


@dataclass
class EnumDef:
    type   : str
    values : set

@dataclass
class AliasDef: # aka type alias
    type : str 
    size : int      # if > 1 then the typedef is a struct with an array of 'size' 
    hint : str = "" # hint on how alias should be printed by Print() method (hex, ascii, etc)

class CppTypesGenerator():
    """
    Takes dict defining enums and alias types and generates C++
    declaration code.

    Enums are added by calling 'add_enum_type()' and aliases are added 
    by calling 'add_alias()'. When all enums and aliases have been 
    added, a C++ generated file can be written by calling 'write_file()'
    """

    def __init__( self ) -> None:
        self.name_to_enum  : typing.Dict[str, EnumDef]  = {}  # enum  name to enum  fields
        self.name_to_alias : typing.Dict[str, AliasDef] = {}  # alias name to alias fields

        self.enums_code_output = ""  # cpp generated enum code goes here
        self.types_code_output = ""  # cpp generated type code goes here


    def add_enum_type( self, enum: dict ) -> None:
        """
        Takes a dict that defines an enum and converts it to cpp code. 
        This method can be called as many times as necessary to add 
        multiple enums.

        Parameters
        ----------
        enum : dict
            A dictionary which defines the enum name, values, type and
            comments. An example input is shown below in yaml format:

                ---------------------------------------------------------
                - name: TransactionType
                  comments: enumeration of transaction types
                  signedness: unsigned
                  size: 2
                  type: enum #TODO: this should change to "enum uint16" and the two above fields removed
                  values:
                  - comments: account key link transaction
                      name: ACCOUNT_KEY_LINK
                      value: 16716
                  - comments: node key link transaction
                      name: NODE_KEY_LINK
                      value: 16972
                  - comments: aggregate complete transaction
                      name: AGGREGATE_COMPLETE
                      value: 16705
                ---------------------------------------------------------

            An example C++ generated code for the above is shown below:

                ---------------------------------------------------------
                /**
                 * enumeration of transaction types
                 */
                enum class TransactionType : uint16_t
                {
                    ACCOUNT_KEY_LINK = 16716,   //< account key link transaction
                    NODE_KEY_LINK = 16972,      //< node key link transaction
                    AGGREGATE_COMPLETE = 16705, //< aggregate complete transaction
                }
                ---------------------------------------------------------
        """

        enum_name = enum["name"]

        if enum_name in self.name_to_enum:
            print(f"Error: Same enum name, '{enum_name}', defined multiple times!\n")

        enum_type = ByteToTypeConverter.size_to_type( enum["size"], enum["signedness"] )
        self.name_to_enum[enum_name] = EnumDef( enum_type, set() )

        if "comments" in enum:
            self.enums_code_output += f'/**\n * {enum["comments"]}\n */\n'

        self.enums_code_output += f'enum class {enum_name} : {enum_type}\n{{\n'

        for value in enum["values"]:
            self.enums_code_output += f'\t{value["name"]} = {value["value"]},' 
            self.enums_code_output += f'//< {value["comments"]}\n' if "comments" in value else "\n"
            self.name_to_enum[enum_name].values.add(value["name"])

        self.enums_code_output += "};\n\n\n"



    def add_alias( self, user_type: dict ) -> None:
        """
        Takes a dict that defines an alias type and converts it to cpp code. 
        This method can be called as many times as necessary to add
        multiple alias types. 

        Parameters
        ----------
        user_type : dict
            A dictionary which defines the alias name, values, type and
            comments. An example input is shown below in yaml format:

                ---------------------------------------------------------
                - name: Hash256
                  comments: 'A type to store 256bit hashes'
                  signedness: unsigned
                  size: 32
                  type: byte #TODO: this should change to "array uint8_t"
                ---------------------------------------------------------

            An example C++ generated code for the above is shown below:

                ---------------------------------------------------------
                using Hash256 = struct Hash256_t { uint8_t data[32]; }; //< A type to store 256bit hashes                
                ---------------------------------------------------------
        """        

        type_name = user_type["name"]

        if type_name in self.name_to_alias:
            print(f"Error: Same type name, '{type_name}', defined multiple times!\n")


        coverted_type = ByteToTypeConverter.size_to_type( user_type["size"], user_type["signedness"] )

        if("byte" != coverted_type):
            self.types_code_output += f'using {type_name} = {coverted_type};' 
            self.name_to_alias[type_name] = AliasDef( coverted_type , 1 )
        else:
            print_hint = user_type["print"] if "print" in user_type else ""
            self.types_code_output += f'using {type_name} = struct {type_name}_t {{ uint8_t data[{user_type["size"]}]; }};' 
            self.name_to_alias[type_name] = AliasDef( coverted_type , user_type["size"], print_hint  )

        self.types_code_output += f'//< {user_type["comments"]}\n' if "comments" in user_type else "\n"



    def write_file( self, file_path: str ) -> None:
        """
        Writes both the generated enums and user defined types to 'file_path'.
        Enums are written first, followed by the user defined types.
        """

        f = open( file_path, "a" )
        f.write("#pragma once\n\n")
        f.write("#include <cstdint>\n")
        f.write("#include <cstdlib>\n\n")

        f.write( self.enums_code_output )
        f.write( self.types_code_output)

        f.close()
