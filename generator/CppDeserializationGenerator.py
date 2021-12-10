import typing

from .CppFieldGenerator import CppFieldGenerator
from .CppTypesGenerator import CppTypesGenerator


class CppDeserializationGenerator():
    """
    Contains methods that can generate C++ deserialization
    code for the different field types like: inline,
    array sized, condition, etc.
    """



    def __init__( self, types: CppTypesGenerator, class_name: str, size_to_arrays : typing.Dict[str, typing.List[str]] ) -> None:
        self.__name_to_enum   = types.name_to_enum
        self.__name_to_type   = types.name_to_type
        self.__size_to_arrays = size_to_arrays
        self.__class_name     = class_name

        self.__add_succ_var   = False
        self.__add_ptr_var    = False

        self.__code_output    = ""



    def normal_field( self, var_type: str, var_name: str, reserved: bool = False ) -> str:
        member_name = CppFieldGenerator.convert_to_field_name(var_name)

        if var_type in self.__name_to_type or var_type in self.__name_to_enum or var_type in CppFieldGenerator.builtin_types:
            self.__add_ptr_var = True
            self.__code_output += f'\tptr = buffer.GetOffsetPtrAndMove( sizeof({var_type}) ); if(!ptr){{ return false; }}\n'

            if var_name in self.__size_to_arrays or reserved:
                self.__code_output += f'\t{var_type} tmp{member_name[1:]} = *( ({var_type}*) ptr );\n\n'
            else:
                self.__code_output += f'\t{member_name} = *( ({var_type}*) ptr );\n\n'
        else:
            self.__add_succ_var = True
            self.__code_output += f'\tsucc = {member_name}.Deserialize( buffer ); if(!succ){{ return false; }}\n'



    def array_field( self, var_type: str, var_name: str, size_var: int ) -> str:

        name     = CppFieldGenerator.convert_to_field_name(var_name)
        size_var = "tmp" + size_var[:1].upper() + size_var[1:] # name of tmp variable containing size of array

        self.__code_output += f'\n\t{name}.resize({size_var});'
        self.__code_output += f'\n\t{name}.shrink_to_fit();'
        self.__code_output += f'\n\tfor( size_t i=0; i<{size_var}; ++i )\n'
        self.__code_output += f'\t{{\n'

        arr_name_with_idx = var_name+"[i]"
        self.__code_output += "\t"
        self.normal_field(var_type, arr_name_with_idx )

        self.__code_output += f'\t}}\n\n'



    def inline_field( self, var_name: str ):
        self.normal_field(var_name, var_name)



    def reserved_field( self, var_type: str, name: str, value: str ):
        member_name = CppFieldGenerator.convert_to_field_name(name)

        self.normal_field(var_type, name, True)
        self.__code_output += f'\tif( {value} != tmp{member_name[1:]} ){{ return false; }}\n'



    def array_sized_field( self, array_name:  str, array_size:        str, 
                                 header_type: str, header_type_field: str, 
                                 enum_type:   str ):

        array_name        = CppFieldGenerator.convert_to_field_name( array_name )
        array_size        = CppFieldGenerator.convert_to_field_name( array_size )
        header_type_field = CppFieldGenerator.convert_to_field_name( header_type_field )

        self.__code_output += f'\tfor( size_t read_size = 0; read_size < {array_size}; )\n\t{{\n'
        self.__code_output += "\t\t// Deserialize header\n"
        self.__code_output += f'\t\t{ header_type } header;\n'
        self.__code_output += f'\t\tRawBuffer tmp = buffer;\n'
        self.__code_output += f'\t\tsucc = header.Deserialize(tmp); if(!succ){{ return false; }}\n\n'

        self.__code_output += "\t\t// Get element type and create type\n"
        self.__code_output += f'\t\t{ enum_type } type = header.{ header_type_field };\n'
        self.__code_output += f'\t\tstd::unique_ptr<ICatbuffer> catbuf = create_type_{ enum_type }( type, header.mEntityBody.mVersion );\n'
        self.__code_output += f'\t\tif( nullptr == catbuf ){{ return false; }}\n\n'

        self.__code_output += "\t\t// Deserialize element and save it\n"
        self.__code_output += f'\t\tconst size_t rsize = buffer.RemainingSize();\n'
        self.__code_output += f'\t\tsucc = catbuf->Deserialize( buffer ); if(!succ){{ return false; }}\n'
        self.__code_output += f'\t\tread_size += (rsize-buffer.RemainingSize());\n'
        self.__code_output += f'\t\t{ array_name }.push_back( std::move(catbuf) );\n\n'

        self.__code_output += "\t\t// Read optional padding\n"
        self.__code_output += f'\t\tconst size_t padding = (8 - uintptr_t(buffer.GetOffsetPtr())%8) % 8;\n' #TODO: Add support for defining padding in yaml 
        self.__code_output += f'\t\tsucc = buffer.MoveOffset(padding); if(!succ){{ return false; }}\n'
        self.__code_output += f'\t\tread_size += padding;\n'
        self.__code_output += f'\t}}\n\n'

        self.__add_succ_var = True



    def array_fill_field( self, array_type: str, array_name: str ):
        array_name = CppFieldGenerator.convert_to_field_name( array_name )

        self.__code_output += f'\twhile( buffer.RemainingSize() )\n\t{{\n\t\t'
        self.__code_output += f'{ array_type } fill;\n\t\t'
        self.__code_output += f'succ = fill.Deserialize( buffer ); if(!succ){{ return false; }}\n\t\t'
        self.__code_output += f'{ array_name }.push_back( fill );\n\t}}\n\n'

        self.__add_succ_var = True



    def condition_field( self, var_name: str, var_type: str, condition: str, union_name: str = "",  ):
        name   = var_name
        if union_name:
            var_name = CppFieldGenerator.convert_to_field_name(var_name)
            name = f'{union_name}.{var_name}'
        else:
            self.__code_output += f'\n\tif( {condition} )\n\t{{\n\t'

        self.normal_field( var_type, name )

        if not union_name:
           self.__code_output += "\t}\n\n"



    def generate( self ) -> str:
        output = f'bool {self.__class_name}::Deserialize( RawBuffer& buffer )\n{{\n'

        if self.__add_ptr_var:
            output += "\tvoid* ptr;\n"

        if self.__add_succ_var:
            output += "\tbool succ;\n"

        output += self.__code_output
        output += "\treturn true;\n"
        output += "}\n\n\n"
        return output
