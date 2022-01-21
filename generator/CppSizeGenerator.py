from .CppFieldGenerator import CppFieldGenerator
from .CppTypesGenerator import CppTypesGenerator



class CppSizeGenerator():


    def __init__( self, types: CppTypesGenerator, class_name: str ) -> None:
        self.__name_to_enum  = types.name_to_enum
        self.__name_to_alias = types.name_to_alias

        self.__code_output  = f'size_t {class_name}::Size( )\n{{\n\tsize_t size=0;\n'


    def normal_field( self, var_type: str, var_name: str ) -> str:
        var_name = CppFieldGenerator.convert_to_field_name(var_name)

        if var_type in self.__name_to_alias or var_type in self.__name_to_enum or var_type in CppFieldGenerator.builtin_types:
            self.__code_output += f'\tsize += sizeof({var_type}); //< {var_name}\n'
        else:
            self.__code_output += f'\tsize += {var_name}.Size();\n'




    def array_field( self, arr_type: str, arr_name: str ) -> str:

        arr_name = CppFieldGenerator.convert_to_field_name( arr_name )

        if arr_type in self.__name_to_enum or arr_type in self.__name_to_alias or arr_type in CppFieldGenerator.builtin_types:
            self.__code_output += f'\tsize += sizeof({arr_type})*{arr_name}.size(); //< {arr_name}\n'
        else:            
            self.__code_output += f'\tif( {arr_name}.size() ){{ size += {arr_name}.size()*{arr_name}[0].Size(); }}\n' #TODO: this is assuming that element sizes are all the same. Maybe do a for loop instead.




    def inline_field( self, var_name: str ):
        var_name = CppFieldGenerator.convert_to_field_name(var_name)
        self.__code_output += f'\tsize += {var_name}.Size();\n'



    def reserved_field( self, var_type: str, var_name: str ):
        self.__code_output += f'\tsize += sizeof({var_type}); //< {var_name}\n'



    def array_sized_field( self, array_name: str, array_size: str ):
        array_name = CppFieldGenerator.convert_to_field_name(array_name)
        array_size = CppFieldGenerator.convert_to_field_name(array_size)

        self.__code_output += f'\tsize += {array_size}; //< {array_name}\n'



    def array_fill_field( self, array_type: str, array_name: str ):
        array_name = CppFieldGenerator.convert_to_field_name( array_name )
        self.__code_output += f'\tsize += {array_name}.size() * sizeof({array_type});\n'



    def condition( self, var_name: str, var_type: str, condition: str, union_name: str = "" ):
        name   = var_name
        if union_name:
            union_name = CppFieldGenerator.convert_to_field_name(union_name)
            self.__code_output += f'\tsize += sizeof({union_name});\n'
        else:
            self.__code_output += f'\n\tif( {condition} )\n\t{{\n\t'
            self.normal_field( var_type, name )

        if not union_name:
           self.__code_output += "\t}\n\n"



    def generate( self ) -> str:
        self.__code_output += "\treturn size;\n"
        self.__code_output += "}\n\n\n"

        return self.__code_output
