import typing

from .CppFieldGenerator import CppFieldGenerator
from .CppTypesGenerator import CppTypesGenerator


class CppSerializationGenerator():
    """
    Contains methods that can generate C++ serialization
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



    def normal_field( self, var_type: str, var_name: str ) -> str:
        member_name = CppFieldGenerator.convert_to_field_name(var_name)

        if var_type in self.__name_to_alias or var_type in self.__name_to_enum or var_type in CppFieldGenerator.builtin_types:
            self.__add_ptr_var = True
            self.__code_output += f'\tptr = buffer.GetOffsetPtrAndMove( sizeof({var_type}) ); if(!ptr){{ return false; }}\n'

            if var_name in self.__size_to_arrays:
                array_name = self.__size_to_arrays[var_name][0]
                array_name = CppFieldGenerator.convert_to_field_name(array_name)
                self.__code_output += f'\t*( ({var_type}*) ptr ) = {array_name}.size();\n\n'
            else:
                self.__code_output += f'\t*( ({var_type}*) ptr ) = {member_name};\n\n'
        else:
            self.__add_succ_var = True
            self.__code_output += f'\tsucc = {member_name}.Serialize( buffer ); if( !succ ){{ return false; }}\n'



    def array_field( self, var_type: str, var_name: str ) -> str:
        member_var = CppFieldGenerator.convert_to_field_name(var_name)

        self.__code_output += f'\n\tfor( size_t i=0; i<{member_var}.size(); ++i )\n'
        self.__code_output += f'\t{{\n'

        arr_name_with_idx = var_name+"[i]"
        self.__code_output += "\t"
        self.normal_field( var_type, arr_name_with_idx )

        self.__code_output += f'\t}}\n\n'



    def inline_field( self, var_name: str ):
        self.normal_field( var_name, var_name )



    def reserved_field( self, var_type: str, var_name: str, value: str ):
        member_var = CppFieldGenerator.convert_to_field_name(var_name)
        self.__code_output += f'\tptr = buffer.GetOffsetPtrAndMove( sizeof({var_type}) ); if(!ptr){{ return false; }}\n'

        tmp = str(value).split()

	#TODO: document this in readme!
        if len(tmp) > 1:
            var_field = CppFieldGenerator.convert_to_field_name(tmp[1])
            value = f'{var_field}.Size()'

        self.__code_output += f'\t*( ({var_type}*) ptr ) = {value}; // {var_type} {member_var}\n\n'
        self.__add_ptr_var  = True



    def array_sized_field( self, array_name: str, align: str = "" ):
        array_name = CppFieldGenerator.convert_to_field_name(array_name)

        self.__code_output += f'\n\tfor( const std::unique_ptr<ICatbuffer>& catbuf : {array_name} )\n\t{{\n'
        self.__code_output += f'  succ = catbuf->Serialize( buffer ); if(!succ){{ return false; }}\n'

        if align:
            self.__code_output += f'  size_t padding = ( {align} - uintptr_t(buffer.GetOffsetPtr())%{align} ) % {align};\n'
            self.__code_output += f'  for( size_t i=0; i<padding; ++i )\n'
            self.__code_output += f'  {{\n'
            self.__code_output += f'    ptr = buffer.GetOffsetPtrAndMove(1); if(!ptr){{ return false; }}\n'
            self.__code_output += f'    *( (uint8_t*) ptr ) = 0;\n'
            self.__code_output += f'  }}\n'
            
        self.__code_output += f' }}\n\n'

        self.__add_ptr_var = True


    def array_fill_field( self, array_type: str, array_name: str ) -> str:
         self.__code_output += f'\tfor( {array_type}& fill : {CppFieldGenerator.convert_to_field_name(array_name)} )\n\t{{\n\t\t'
         self.__code_output += f'succ = fill.Serialize( buffer ); if(!succ){{ return false; }}\n\t}}\n\n'

         self.__add_succ_var = True



    def condition_field( self, var_name: str, var_type: str, condition: str, union_name: str ):
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
        output = f'bool {self.__class_name}::Serialize( RawBuffer& buffer )\n{{\n'

        if self.__add_ptr_var:
            output += "\tvoid* ptr;\n"

        if self.__add_succ_var:
            output += "\tbool succ;\n"

        output += self.__code_output
        output += "\treturn true;\n"
        output += "}\n\n\n"
        return output
