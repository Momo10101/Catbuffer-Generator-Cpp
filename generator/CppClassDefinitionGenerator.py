import typing

from .CppClassDeclarationGenerator import CppClassDeclarationGenerator
from .CppFieldGenerator import CppFieldGenerator
from .CppTypesGenerator import CppTypesGenerator



class CppClassDefinitionGenerator():
    """
    Takes a C++ class declaration and generates class definition code.
    The generated code consist of header includes and
    an implementation of the size and serialization/deserialization
    ICatBuffer inherited methods.

    A C++ generated implementation file can be written by calling
    'write_file()'.
    """

    def __init__( self, 
                  class_decl:               CppClassDeclarationGenerator, 
                  class_name_to_class_decl: typing.Dict[str, CppClassDeclarationGenerator],
                  types:                    CppTypesGenerator ) -> None:
        """
        Parameters
        ----------
        class_decl : CppClassDeclarationGenerator
            The class declaration which will be used for knowing what
            should be serialized and deserialized

        class_name_to_class_decl: typing.Dict[str, CppClassDeclarationGenerator]
            A list of all class declarations, used for type checking 

        types : CppTypesGenerator
            A list of all user defined types, used for type checking
        """

        self.__class_decl                  = class_decl
        self.__class_name_to_class_decl    = class_name_to_class_decl
 
        self.__includes                    = set()

        self.__include_code_output         = ""
        self.deserialization_body          = ""
        self.serialization_body            = ""
        self.__size_code_output            = ""

        self.__deserializer   = CppDeserializationGenerator( types )
        self.__serializer     = CppSerializationGenerator( types )
        self.__size_generator = CppSizeGenerator( types )

        self.__types          = types

        self.__generate_implementation()


    def write_file( self, file_path: str ):
        self.__generate_includes()

        f = open( file_path, "w" )
        f.write( self.__include_code_output )
        f.write( self.__deserialization_code_output )
        f.write( self.__serialization_code_output )
        f.write( self.__size_code_output )


    def __generate_implementation( self ):
        """
        Goes through fields of types 'const', 'inline', 'reserved', 
        'array', 'array sized', 'array fill' and 'condition' and 
        generates corresponding C++ serialization and deserialization
        methods.
        """

        class_name   = self.__class_decl.class_name
        fields       = self.__class_decl.fields
        conditions   = self.__class_decl.conditions.copy()

        self.__includes.add( f'#include "{class_name}.h"' )

        self.__deserialization_code_output = f'bool {class_name}::Deserialize( RawBuffer& buffer )\n{{\n'
        self.__serialization_code_output   = f'bool {class_name}::Serialize( RawBuffer& buffer )\n{{\n'
        self.__size_code_output            = f'size_t {class_name}::Size( )\n{{\n\tsize_t size=0;\n'

        deserialization_body = ""
        serialization_body   = ""

        add_succ_var = False
        add_ptr_var  = False

        for field in fields:
            var_type = field["type"]
            name     = field["name"] if "name" in field else var_type
            size     = field["size"] if "size" in field else ""


            if "disposition" in field:

                if "const" == field["disposition"]:
                    continue # const fields dont need serialization/deserialization
                
                elif "array" == field["disposition"]:
                    deserialization_body    += self.__deserializer.array_field( var_type, name, size )
                    serialization_body      += self.__serializer.array_field( var_type, name, size )
                    self.__size_code_output += self.__size_generator.array_field( var_type, name, size )

                    if var_type in self.__types.name_to_type or var_type in self.__types.name_to_enum or var_type in CppFieldGenerator.builtin_types:
                        add_ptr_var = True
                    else:
                        add_succ_var = True

                elif "inline" == field["disposition"]:
                    deserialization_body    += self.__deserializer.inline_field( name )
                    serialization_body      += self.__serializer.inline_field( name )
                    self.__size_code_output += self.__size_generator.inline_field( name )
                    add_succ_var = True

                elif "reserved" == field["disposition"]:
                    deserialization_body    += self.__deserializer.reserved_field( var_type, name )
                    serialization_body      += self.__serializer.reserved_field( var_type, name )
                    self.__size_code_output += self.__size_generator.reserved_field( var_type, name )
                    add_ptr_var = True

                elif "array sized" == field["disposition"]:
                    header_type       = field["header"]
                    header_type_field = field["header_type_field"]
                    enum_type         = self.__get_var_type( header_type_field, header_type )

                    deserialization_body    += self.__deserializer.array_sized_field( name, size, header_type, header_type_field, enum_type )
                    serialization_body      += self.__serializer.array_sized_field( name )
                    self.__size_code_output += self.__size_generator.array_sized_field( name, size )

                    self.__includes.add(f'#include "converters.h"')
                    add_succ_var = True

                elif "array fill" == field["disposition"]: #TODO: check that only added once and at the end!!
                    deserialization_body    += self.__deserializer.array_fill_field( var_type, name )
                    serialization_body      += self.__serializer.array_fill_field( var_type, name )
                    self.__size_code_output += self.__size_generator.array_fill_field( var_type, name )
                    add_succ_var = True
            else:

                if var_type in self.__types.name_to_type or var_type in self.__types.name_to_enum or var_type in CppFieldGenerator.builtin_types:
                    add_ptr_var = True
                else:
                    add_succ_var = True

                if "condition" in field:
                    condition_name = field["condition"]
                    if condition_name in conditions:
                        condition  = self.__gen_condition_from_field(conditions[condition_name][0])
                        union_name = "" if len(conditions[condition_name]) == 1 else condition_name+"_union"

                        deserialization_body    += self.__deserializer.condition( name, var_type, condition, union_name )
                        serialization_body      += self.__serializer.condition_field( name, var_type, condition, union_name )
                        self.__size_code_output += self.__size_generator.condition( name, var_type, condition, union_name )

                        del conditions[condition_name]

                else:
                    deserialization_body    += self.__deserializer.normal_field( var_type, name )
                    serialization_body      += self.__serializer.normal_field( var_type, name )
                    self.__size_code_output += self.__size_generator.normal_field( var_type, name )


        if add_ptr_var:
            self.__deserialization_code_output += "\tvoid* ptr;\n"
            self.__serialization_code_output   += "\tvoid* ptr;\n"

        if add_succ_var:
            self.__deserialization_code_output += "\tbool succ;\n"
            self.__serialization_code_output   += "\tbool succ;\n"

        self.__deserialization_code_output += deserialization_body
        self.__deserialization_code_output += "\treturn true;\n"
        self.__deserialization_code_output += "}\n\n\n"

        self.__serialization_code_output   += serialization_body
        self.__serialization_code_output   += "\treturn true;\n"
        self.__serialization_code_output   += "}\n\n\n"


        self.__size_code_output += "\treturn size;\n"
        self.__size_code_output += "}\n"

    def __get_var_type( self, var_name: str, class_name: str ) -> str:
        """
        Given a class member variable name and a class name, will return
        the type of the variable member in that class. In other words, 
        returns the type of a member variable in a class.
        """

        if class_name not in self.__class_name_to_class_decl:
            print(f'Error: {class_name} not found in classes\n')
            exit(1)

        for elem in self.__class_name_to_class_decl[class_name].fields:
            if "name" not in elem:
                continue

            if elem["name"] == var_name:
                return elem["type"]

        print(f'Error: Variable "{var_name}" not found in class "{class_name}"\n')
        exit(1)


    def __generate_includes( self ) -> str:

        for include in self.__includes:
            self.__include_code_output += (include + "\n")

        self.__include_code_output += '\n'


    def __gen_condition_from_field( self, field: dict) -> str:
        op = ""

        if( "not equals" == field["condition_operation"] ):
            op = "!="
        elif( "equals" == field["condition_operation"] ):
            op = "=="
        else:
            print(f'Error: unknown condition operator "{field["condition_operation"]}"')

        return f'{CppFieldGenerator.convert_to_field_name(field["condition"])} {op} {field["condition_value"]}'



class CppDeserializationGenerator():
    """
    Contains methods that can generate C++ deserialization
    code for the different field types like: inline,
    array sized, condition, etc.
    """


    def __init__( self, types: CppTypesGenerator ) -> None:
        self.__name_to_enum = types.name_to_enum
        self.__name_to_type = types.name_to_type


    def normal_field( self, var_type: str, name: str ) -> str:
        name   = CppFieldGenerator.convert_to_field_name(name)
        output = ""

        if var_type in self.__name_to_type or var_type in self.__name_to_enum or var_type in CppFieldGenerator.builtin_types:
            output += f'\tptr = buffer.GetOffsetPtrAndMove( sizeof({var_type}) ); if(!ptr){{ return false; }}\n'
            output += f'\t{name} = *( ({var_type}*) ptr );\n\n'
        else:
            output += f'\tsucc = {name}.Deserialize( buffer ); if(!succ){{ return false; }}\n'

        return output


    def array_field( self, var_type: str, var_name: str, size_var: int) -> str:

        name     = CppFieldGenerator.convert_to_field_name(var_name)
        size_var = CppFieldGenerator.convert_to_field_name(size_var) # name of field containing size of array

        output  = f'\n\t{name}.resize({size_var});'
        output += f'\n\t{name}.shrink_to_fit();'
        output += f'\n\tfor( size_t i=0; i<{size_var}; ++i )\n'
        output += f'\t{{\n'

        arr_name_with_idx = var_name+"[i]"
        output += "\t"+self.normal_field(var_type, arr_name_with_idx )

        output += f'\t}}\n\n'

        return output


    def inline_field( self, var_name: str ):
        return self.normal_field(var_name, var_name)

    def reserved_field( self, var_type: str, name: str ):
        return self.normal_field(var_type, name)


    def array_sized_field( self, array_name: str, array_size: str, 
                                 header_type: str, header_type_field: str, 
                                 enum_type: str ):

        array_name        = CppFieldGenerator.convert_to_field_name( array_name )
        array_size        = CppFieldGenerator.convert_to_field_name( array_size )
        header_type_field = CppFieldGenerator.convert_to_field_name( header_type_field )

        output  = f'\tfor( size_t read_size = 0; read_size < {array_size}; )\n\t{{\n'
        output += "\t\t// Deserializ header\n"
        output += f'\t\t{ header_type } header;\n'
        output += f'\t\tRawBuffer tmp = buffer;\n'
        output += f'\t\tsucc = header.Deserialize(tmp); if(!succ){{ return false; }}\n\n'

        output += "\t\t// Get element type and create type\n"
        output += f'\t\t{ enum_type } type = header.{ header_type_field };\n'
        output += f'\t\tstd::unique_ptr<ICatbuffer> catbuf = create_type_{ enum_type }( type );\n\n'

        output += "\t\t// Deserialize element and save it\n"
        output += f'\t\tconst size_t rsize = buffer.RemainingSize();\n'
        output += f'\t\tsucc = catbuf->Deserialize( buffer ); if(!succ){{ return false; }}\n'
        output += f'\t\tread_size += (rsize-buffer.RemainingSize());\n'
        output += f'\t\t{ array_name }.push_back( std::move(catbuf) );\n\n'

        output += "\t\t// Read optional padding\n"
        output += f'\t\tconst size_t padding = (8 - uintptr_t(buffer.GetOffsetPtr())%8) % 8;\n' #TODO: Add support for defining padding in yaml 
        output += f'\t\tsucc = buffer.MoveOffset(padding); if(!succ){{ return false; }}\n'
        output += f'\t\tread_size += padding;\n'
        output += f'\t}}\n\n'

        return output


    def array_fill_field( self, array_type: str, array_name: str ):
        array_name = CppFieldGenerator.convert_to_field_name( array_name )

        output  = f'\twhile( buffer.RemainingSize() )\n\t{{\n\t\t'
        output += f'{ array_type } fill;\n\t\t'
        output += f'succ = fill.Deserialize( buffer ); if(!succ){{ return false; }}\n\t\t'
        output += f'{ array_name }.push_back( fill );\n\t}}\n\n'

        return output


    def condition( self, var_name: str, var_type: str, condition: str, union_name: str = "",  ):
        output = ""
        name   = var_name
        if union_name:
            var_name = CppFieldGenerator.convert_to_field_name(var_name)
            name = f'{union_name}.{var_name}'
        else:
            output += f'\n\tif( {condition} )\n\t{{\n\t'

        output += self.normal_field( var_type, name )

        if not union_name:
           output += "\t}\n\n"

        return output



class CppSerializationGenerator():
    """
    Contains methods that can generate C++ serialization
    code for the different field types like: inline,
    array sized, condition, etc.
    """


    def __init__( self, types: CppTypesGenerator ) -> None:
        self.__name_to_enum = types.name_to_enum
        self.__name_to_type = types.name_to_type


    def normal_field( self, var_type: str, var_name: str ) -> str:
        var_name = CppFieldGenerator.convert_to_field_name(var_name)
        output = ""

        if var_type in self.__name_to_type or var_type in self.__name_to_enum or var_type in CppFieldGenerator.builtin_types:
            output += f'\tptr = buffer.GetOffsetPtrAndMove( sizeof({var_type}) ); if(!ptr){{ return false; }}\n'
            output += f'\t*( ({var_type}*) ptr ) = {var_name};\n\n'
        else:
            output += f'\tsucc = {var_name}.Serialize( buffer ); if( !succ ){{ return false; }}\n'

        return output


    def array_field( self, var_type: str, var_name: str, array_size_name: int) -> str:
        #var_name = CppFieldGenerator.convert_to_field_name(var_name)
        size_var = CppFieldGenerator.convert_to_field_name(array_size_name) # name of field containing size of array

        output  = f'\n\tfor( size_t i=0; i<{size_var}; ++i )\n'
        output += f'\t{{\n'

        arr_name_with_idx = var_name+"[i]"
        output += "\t"+self.normal_field( var_type, arr_name_with_idx )

        output += f'\t}}\n\n'

        return output


    def inline_field( self, var_name: str ):
        return self.normal_field( var_name, var_name )


    def reserved_field( self, var_type: str, var_name: str ):
        return self.normal_field( var_type, var_name )


    def array_sized_field( self, array_name: str ):
        array_name = CppFieldGenerator.convert_to_field_name(array_name)

        output  = f'\n\tfor( const std::unique_ptr<ICatbuffer>& catbuf : {array_name} )\n\t{{\n\t\t'
        output += f'succ = catbuf->Serialize( buffer ); if(!succ){{ return false; }}\n\t\t'
        output += f'size_t padding = ( 8 - uintptr_t(buffer.GetOffsetPtr())%8 ) % 8;\n\t\t'

        output += f'for( size_t i=0; i<padding; ++i )\n\t\t{{\n'
        output += f'\t\t\tptr = buffer.GetOffsetPtrAndMove(1); if(!ptr){{ return false; }}\n'
        output += f'\t\t\t*( (uint8_t*) ptr ) = 0;\n\t\t}}\n\t}}\n\n'

        return output


    def array_fill_field( self, array_type: str, array_name: str ) -> str:
         output  = f'\tfor( {array_type}& fill : {CppFieldGenerator.convert_to_field_name(array_name)} )\n\t{{\n\t\t'
         output += f'succ = fill.Serialize( buffer ); if(!succ){{ return false; }}\n\t}}\n\n'

         return output


    def condition_field( self, var_name: str, var_type: str, condition: str, union_name: str ):
        output = ""
        name   = var_name
        if union_name:
            var_name = CppFieldGenerator.convert_to_field_name(var_name)
            name = f'{union_name}.{var_name}'
        else:
            output += f'\n\tif( {condition} )\n\t{{\n\t'

        output += self.normal_field( var_type, name )

        if not union_name:
           output += "\t}\n\n"

        return output



class CppSizeGenerator():

    def __init__( self, types: CppTypesGenerator ) -> None:
        self.__name_to_enum = types.name_to_enum
        self.__name_to_type = types.name_to_type


    def normal_field( self, var_type: str, var_name: str ) -> str:
        var_name = CppFieldGenerator.convert_to_field_name(var_name)
        output   = ""

        if var_type in self.__name_to_type or var_type in self.__name_to_enum or var_type in CppFieldGenerator.builtin_types:
            output += f'\tsize += sizeof({var_name}); //< {var_name}\n'
        else:
            output += f'\tsize += {var_name}.Size();\n'

        return output


    def array_field( self, arr_type: str, arr_name: str, size_var: int ) -> str:

        arr_name = CppFieldGenerator.convert_to_field_name( arr_name )
        size_var = CppFieldGenerator.convert_to_field_name( size_var ) # name of field containing size of array
        output   = ""

        if arr_type in self.__name_to_enum or arr_type in self.__name_to_type or arr_type in CppFieldGenerator.builtin_types:
            output += f'\tsize += sizeof({arr_type})*{size_var}; //< {arr_name}\n'
        else:            
            output += f'\tif( {arr_name}.size() ){{ size += {arr_name}.size()*{arr_name}[0].Size(); }}\n' #TODO: this is assuming that element sizes are all the same. Maybe do a for loop instead.

        return output


    def inline_field( self, var_name: str ):
        var_name = CppFieldGenerator.convert_to_field_name(var_name)
        return f'\tsize += {var_name}.Size();\n'


    def reserved_field( self, var_type: str, var_name: str ):
        return f'\tsize += sizeof({var_type}); //< {var_name}\n'


    def array_sized_field( self, array_name: str, array_size: str ):
        array_name = CppFieldGenerator.convert_to_field_name(array_name)
        array_size = CppFieldGenerator.convert_to_field_name(array_size)

        return f'\tsize += {array_size}; //< {array_name}\n'


    def array_fill_field( self, array_type: str, array_name: str ):
        array_name = CppFieldGenerator.convert_to_field_name( array_name )
        return f'\tsize += {array_name}.size() * sizeof({array_type});\n'

    def condition( self, var_name: str, var_type: str, condition: str, union_name: str = "" ):
        output = ""
        name   = var_name
        if union_name:
            union_name = CppFieldGenerator.convert_to_field_name(union_name)
            output = f'\tsize += sizeof({union_name});\n'
        else:
            output += f'\n\tif( {condition} )\n\t{{\n\t'
            output += self.normal_field( var_type, name )

        if not union_name:
           output += "\t}\n\n"

        return output
