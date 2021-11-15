import typing

from .CppFieldGenerator import ByteToTypeConverter


class CppTypesGenerator():
    """
    Takes dict defining enums and user defined types and generates C++
    declaration code.

    Enums are added by calling 'add_enum_type()' and types are added 
    by calling 'add_user_type()'. When all enums and types have been 
    added, a C++ generated file can be written by calling 'write_file()'
    """

    def __init__( self ) -> None:
        self.name_to_enum : typing.Dict[str, dict] = {}  # enum name to enum fields
        self.name_to_type : typing.Dict[str, dict] = {}  # type name to type fields

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

        self.name_to_enum[enum_name] = enum

        if "comments" in enum:
            self.enums_code_output += f'/**\n * {enum["comments"]}\n */\n'

        type = ByteToTypeConverter.size_to_type( enum["size"], enum["signedness"] )
        self.enums_code_output += f'enum class {enum_name} : {type}\n{{\n'

        for value in enum["values"]:
            self.enums_code_output += f'\t{value["name"]} = {value["value"]},' 
            self.enums_code_output += f'//< {value["comments"]}\n' if "comments" in value else "\n"

        self.enums_code_output += "};\n\n\n"



    def add_user_type( self, user_type: dict ) -> None:
        """
        Takes a dict that defines a user defined type and converts it to cpp code. 
        This method can be called as many times as necessary to add
        multiple user defined types. 

        Parameters
        ----------
        user_type : dict
            A dictionary which defines the type name, values, type and
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

        if type_name in self.name_to_type:
            print(f"Error: Same type name, '{type_name}', defined multiple times!\n")

        self.name_to_type[type_name] = user_type

        coverted_type = ByteToTypeConverter.size_to_type( user_type["size"], user_type["signedness"] )

        if("byte" != coverted_type):
            self.types_code_output += f'using {type_name} = {coverted_type};' 
        else:
            self.types_code_output += f'using {type_name} = struct {type_name}_t {{ uint8_t data[{user_type["size"]}]; }};' 

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