import typing

from .CppFieldGenerator import CppFieldGenerator
from .CppTypesGenerator import CppTypesGenerator


class CppPrintOutputGenerator():
    """
    Generates a 'Print()' C++ method to pretty print deserialized raw byte buffer inputs.
    Fields are added for printing by calling 'xyz_field()' methods and when done the C++ 
    print method is generated by calling the 'generate()' method.
    """

    def __init__( self, types: CppTypesGenerator, class_name: str, size_to_arrays : typing.Dict[str, typing.List[str]] ) -> None:
        self.__name_to_enum   = types.name_to_enum
        self.__name_to_alias  = types.name_to_alias
        self.__size_to_arrays = size_to_arrays

        self.__code_output   = f'void {class_name}::Print( size_t level )\n{{\n'
        self.__code_output  += f"\tstd::string tabs( level, '\\t' );\n"
        self.__code_output  += f'\tstd::cout << tabs << "{class_name} (" << Size() <<" bytes)\\n";\n'
        self.__code_output  += f'\tstd::cout << tabs << "{{\\n";\n\n'


    def normal_field( self, var_type: str, var_name: str, print_hint: str = "" ):
        member_name = CppFieldGenerator.convert_to_field_name(var_name)

        if var_type in self.__name_to_alias:
            typedef = self.__name_to_alias[var_type]

            if typedef.size == 1:
                self.__code_output += f'\tstd::cout << tabs << "\\t{var_type} {member_name}: " << +(static_cast<{typedef.type}>({member_name})) << " (" << sizeof({member_name}) <<" bytes)\\n";\n'
            else:
                print_mod, separator = get_print_mod(typedef.hint)

                self.__code_output += f'\n\t{{'
                self.__code_output += f'\tstd::ios_base::fmtflags flags( std::cout.flags() );\n'
                self.__code_output += f'\tstd::cout << tabs << "\\t{typedef.type} " << "{member_name}[ " << {typedef.size} << " ] = ";\n'
                self.__code_output += f'\tfor( size_t j=0; j<{typedef.size}; ++j )\n'
                self.__code_output += f'\t{{\n'
                self.__code_output += f'\t\tstd::cout <<  {print_mod}{member_name}.data[j] {separator};\n'
                self.__code_output += f'\t}}\n'
                self.__code_output += f'\tstd::cout.flags( flags );\n\t}}\n'
                self.__code_output += f'\tstd::cout <<  " (" << sizeof({member_name}) <<" bytes)\\n";\n'

        elif var_type in self.__name_to_enum:
            enum_type = self.__name_to_enum[var_type].type
            self.__code_output += f'\tstd::cout << tabs << "\\t{var_type} {member_name}: " << +static_cast<{enum_type}>({member_name}) << " (" << sizeof({member_name}) <<" bytes)\\n";\n'

        elif var_type in CppFieldGenerator.builtin_types:

            if var_name in self.__size_to_arrays:
                array_name = self.__size_to_arrays[var_name][0]
                array_name = CppFieldGenerator.convert_to_field_name(array_name)
                self.__code_output += f'\tstd::cout << tabs << "\\t{var_type} {member_name}: " << {array_name}.size() << " (" << sizeof({var_type}) <<" bytes)\\n";\n'
            else:
                print_mod, _ = get_print_mod(print_hint)
                self.__code_output += f'\n\t{{'
                self.__code_output += f'\tstd::ios_base::fmtflags flags( std::cout.flags() );\n'
                self.__code_output += f'\tstd::cout << tabs << "\\t{var_type} {member_name}: " << {print_mod}{member_name} << " (" << sizeof({member_name}) <<" bytes)\\n";\n'
                self.__code_output += f'\tstd::cout.flags( flags );\n\t}}\n'

        else:
            self.__code_output += f'\t{member_name}.Print( level+1 );\n'



    def array_field( self, array_type: str, array_name: str, print_hint: str = "" ):
        arr_member_name = CppFieldGenerator.convert_to_field_name( array_name )

        self.__code_output += f'\n'
        self.__code_output += f'\tstd::cout << tabs << "\\t{array_type} " << "{arr_member_name}[ " << {arr_member_name}.size() << " ] =\\n";\n' 
        self.__code_output += f'\tstd::cout << tabs << "\\t[\\n";\n'
        self.__code_output += f'\tfor( size_t i=0; i<{arr_member_name}.size(); ++i )\n'
        self.__code_output += f'\t{{\n'

        self.normal_field(array_type, array_name+'[i]', print_hint)

        self.__code_output += f'\t}}\n'
        self.__code_output += f'\tstd::cout << tabs <<"\\t] (" << sizeof({array_type}) * {arr_member_name}.size() <<" bytes)\\n";\n'



    def inline_field( self, var_name: str ):
        var_name = CppFieldGenerator.convert_to_field_name(var_name)
        self.__code_output += f'\t{var_name}.Print( level+1 );\n'



    def reserved_field( self, var_type: str, var_name: str, var_value: str ):
        self.__code_output += f'\tstd::cout << tabs << "\\t{var_type} {var_name}: " << {var_value} << " (" << sizeof({var_type}) <<" bytes)\\n";\n'



    def array_sized_field( self, array_type: str, array_name: str, array_size: str ):
        array_name = CppFieldGenerator.convert_to_field_name(array_name)
        array_size = CppFieldGenerator.convert_to_field_name(array_size)

        self.__code_output += f'\tstd::cout << tabs << "\\t{array_type} " << "{array_name}[ " << {array_name}.size() << " ] =\\n";\n' 
        self.__code_output += f'\tstd::cout << tabs << "\\t[\\n";\n'
        self.__code_output += f'\tfor( size_t i=0; i<{array_name}.size(); ++i )\n'
        self.__code_output += f'\t{{\n'
        self.__code_output += f'\t\t{array_name}[i]->Print( level+1 );'
        self.__code_output += f'\t}}\n'



    def array_fill_field( self, array_type: str, array_name: str ):
        self.array_field( array_type, array_name )



    def condition( self, var_type: str, var_name: str, condition: str, union_name: str = "" ):
        self.__code_output += f'\tstd::cout << tabs << "\\tTODO: to be implemented when unions implemented in schemas!!!: if( {condition} ) {var_type} {var_name}\\n";\n'
        #TODO: implement this when unions and 



    def generate( self ) -> str:
        self.__code_output  += '\n\tstd::cout << tabs << "}\\n";\n'
        self.__code_output  += "}\n"
        return self.__code_output



def get_print_mod( print_hint: str ):
    if print_hint == "hex":
        print_mod = "std::setfill(\'0\') << std::setw(2) << std::hex << +"
        separator = ''
    elif print_hint == "ascii":
        print_mod = ""
        separator = ''
    elif print_hint == "num" or print_hint == "": 
        print_mod = "+"
        separator = '<< "|"'
    else:
        print(f"Error: Unknown hint '{print_hint}' !")
        exit(1)

    return print_mod, separator
