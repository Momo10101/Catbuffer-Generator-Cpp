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
        self.__name_to_alias  = types.name_to_alias
        self.__size_to_arrays = size_to_arrays
        self.__class_name     = class_name

        self.__add_succ_var   = False
        self.__add_ptr_var    = False

        self.__code_output    = ""



    def normal_field( self, var_type: str, var_name: str, reserved: bool = False ) -> str:
        member_name = CppFieldGenerator.convert_to_field_name(var_name)

        if var_type in self.__name_to_alias or var_type in self.__name_to_enum or var_type in CppFieldGenerator.builtin_types:
            self.__add_ptr_var = True
            self.__code_output += f'\tptr = buffer.GetOffsetPtrAndMove( sizeof({var_type}) ); if(!ptr){{ return false; }}\n'

            if var_name in self.__size_to_arrays or reserved:
                self.__code_output += f'\t{var_type} tmp{member_name[1:]} = *( ({var_type}*) ptr );\n\n'
            else:
                self.__code_output += f'\t{member_name} = *( ({var_type}*) ptr );\n\n'
        else:
            self.__add_succ_var = True
            self.__code_output += f'\tsucc = {member_name}.Deserialize( buffer ); if(!succ){{ return false; }}\n'



    def array_field( self, var_type: str, var_name: str, size_var: str, size_type: str ) -> str:

        name = CppFieldGenerator.convert_to_field_name(var_name)

        if not str(size_var).isdigit():
            #TODO: disabled for now due to NEM incompatibility (see also CppClassDeclarationConstructor.init() method) 
            #size_var = "tmp" + size_var[:1].upper() + size_var[1:] # name of tmp variable containing size of array
            size_var = CppFieldGenerator.convert_to_field_name(size_var) #TODO: use above line instead when NEM incompatibility has been solved


            self.__code_output += f'\n\tif( {size_var} != std::numeric_limits<{size_type}>::max() )\n\t{{'
        self.__code_output += f'\n\t\t{name}.resize({size_var});'
        self.__code_output += f'\n\t\t{name}.shrink_to_fit();'
        self.__code_output += f'\n\t\tfor( size_t i=0; i<{size_var}; ++i )\n'
        self.__code_output += f'\t\t{{\n'

        arr_name_with_idx = var_name+"[i]"
        self.__code_output += "\t"
        self.normal_field(var_type, arr_name_with_idx )

        self.__code_output += f'\t\t}}\n\n'

        if not str(size_var).isdigit():
            self.__code_output += f'\t}}\n'


    def inline_field( self, var_name: str ):
        self.normal_field(var_name, var_name)



    def reserved_field( self, var_type: str, name: str, value: str ):
        member_name = CppFieldGenerator.convert_to_field_name(name)

        self.normal_field(var_type, name, True)

        tmp = str(value).split()
        if len(tmp) > 1:
            var_field = CppFieldGenerator.convert_to_field_name(tmp[1])
            value = f'{var_field}.Size()'
            self.__code_output += f'(void) tmp{member_name[1:]};'

        if len(tmp) == 1:
            self.__code_output += f'\tif( {value} != tmp{member_name[1:]} ){{ return false; }}\n'



    def array_sized_field( self, array_name:  str, array_size:        str, 
                                 header_type: str, header_type_field: str, header_version_field: str,
                                 enum_type:   str, align:             str = "" ):

        array_name           = CppFieldGenerator.convert_to_field_name( array_name )
        array_size           = CppFieldGenerator.convert_to_field_name( array_size )
        header_type_field    = CppFieldGenerator.convert_to_field_name( header_type_field )
        header_version_field = CppFieldGenerator.convert_to_field_name( header_version_field )

        self.__code_output += f'\tfor( size_t read_size = 0; read_size < {array_size}; )\n\t{{\n'
        self.__code_output += "\t\t// Deserialize header\n"
        self.__code_output += f'\t\t{ header_type } header;\n'
        self.__code_output += f'\t\tRawBuffer tmp = buffer;\n'
        self.__code_output += f'\t\tsucc = header.Deserialize(tmp); if(!succ){{ return false; }}\n\n'

        self.__code_output += "\t\t// Get element type and create type\n"
        self.__code_output += f'\t\t{ enum_type } type = header.{ header_type_field };\n'
        self.__code_output += f'\t\tstd::unique_ptr<ICatbuffer> catbuf = create_type_{ enum_type }( type, header.{header_version_field} );\n'
        self.__code_output += f'\t\tif( nullptr == catbuf ){{ return false; }}\n\n'

        self.__code_output += "\t\t// Deserialize element and save it\n"
        self.__code_output += f'\t\tconst size_t rsize = buffer.RemainingSize();\n'
        self.__code_output += f'\t\tsucc = catbuf->Deserialize( buffer ); if(!succ){{ return false; }}\n'
        self.__code_output += f'\t\tread_size += (rsize-buffer.RemainingSize());\n'
        self.__code_output += f'\t\t{ array_name }.push_back( std::move(catbuf) );\n\n'

        if align:
            self.__code_output += "\t\t// Read optional padding\n"
            self.__code_output += f'\t\tconst size_t padding = ({align} - uintptr_t(buffer.GetOffsetPtr())%{align}) % {align};\n'
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



    def condition_field( self, var_name: str, var_type: str, condition: str, union_name: str = "" ):
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
