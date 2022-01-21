import typing

from .CppClassDeclarationGenerator import CppClassDeclarationGenerator
from .CppFieldGenerator import CppFieldGenerator
from .CppTypesGenerator import CppTypesGenerator
from .CppPrintOutputGenerator import CppPrintOutputGenerator
from .CppSerializationGenerator import CppSerializationGenerator
from .CppDeserializationGenerator import CppDeserializationGenerator
from .CppSizeGenerator import CppSizeGenerator



class CppClassDefinitionGenerator():
    """
    Takes a C++ class declaration and generates class definition code.
    The generated code consist of header includes and
    an implementation of the size and serialization/deserialization
    ICatBuffer inherited methods.

    A C++ generated implementation file can be written by calling
    'write_file()'.
    """



    def init( self, 
              class_decl:               CppClassDeclarationGenerator, 
              class_name_to_class_decl: typing.Dict[str, CppClassDeclarationGenerator],
              types:                    CppTypesGenerator,
              prettyprinter:            bool = False ) -> None:
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

        prettyprinter: bool, optional
            Set to true for pretty printing functionality
        """

        self.__class_decl                  = class_decl
        self.__class_name_to_class_decl    = class_name_to_class_decl
        self.__types                       = types

        self.__includes                    = set()
        self.__include_code_output         = ""

        self.__prettyprinter               = prettyprinter

        self.__deserializer                = CppDeserializationGenerator( types, class_decl.class_name, class_decl.size_to_arrays )
        self.__serializer                  = CppSerializationGenerator( types, class_decl.class_name, class_decl.size_to_arrays )
        self.__size_generator              = CppSizeGenerator( types, class_decl.class_name )
        self.__print_generator             = CppPrintOutputGenerator( types, class_decl.class_name, class_decl.size_to_arrays )

        self.__generate_implementation()



    def write_file( self, file_path: str ):
        self.__generate_includes()

        f = open( file_path, "w" )
        f.write( self.__include_code_output )
        f.write( self.__deserializer.generate() )
        f.write( self.__serializer.generate() )
        f.write( self.__size_generator.generate() )

        if self.__prettyprinter:
            f.write( self.__print_generator.generate() )



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

        for field in fields:
            var_type   = field["type"]
            name       = field["name"]  if "name"  in field else var_type
            size       = field["size"]  if "size"  in field else ""
            print_hint = field["print"] if "print" in field else ""


            if "disposition" in field:

                disposition = field["disposition"]

                if "const" == disposition:
                    continue # const fields dont need serialization/deserialization

                elif( "struct_type" == disposition ):
                    continue

                elif "array" == disposition:
                    size_var_type = ""
                    if size in self.__class_decl.member_vars:
                        _, size_var_type = self.__class_decl.member_vars[size]

                    self.__deserializer.array_field( var_type, name, size, size_var_type)
                    self.__serializer.array_field( var_type, name )
                    self.__size_generator.array_field( var_type, name )
                    self.__print_generator.array_field( var_type, name, print_hint )

                elif "inline" == disposition:
                    self.__deserializer.inline_field( name )
                    self.__serializer.inline_field( name )
                    self.__size_generator.inline_field( name )
                    self.__print_generator.inline_field( name )

                elif "reserved" == disposition:
                    reserved_value = field["value"]
                    self.__deserializer.reserved_field( var_type, name, reserved_value )
                    self.__serializer.reserved_field( var_type, name, reserved_value )
                    self.__size_generator.reserved_field( var_type, name )
                    self.__print_generator.reserved_field( var_type, name, reserved_value)

                elif "array_sized" == disposition:
                    header_type          = field["type"]
                    header_type_field    = field["header_type_field"]
                    header_version_field = field["header_version_field"]
                    enum_type            = self.__get_var_type( header_type_field, header_type )
                    align                = field["align"] if "align" in field else ""

                    self.__deserializer.array_sized_field( name, size, header_type, header_type_field, header_version_field, enum_type, align )
                    self.__serializer.array_sized_field( name, align )
                    self.__size_generator.array_sized_field( name, size )
                    self.__print_generator.array_sized_field( header_type, name, size )

                    self.__includes.add(f'#include "converters.h"')

                elif "array_fill" == disposition: #TODO: check that only added once and at the end!!
                    self.__deserializer.array_fill_field( var_type, name )
                    self.__serializer.array_fill_field( var_type, name )
                    self.__size_generator.array_fill_field( var_type, name )
                    self.__print_generator.array_fill_field( var_type, name )
                else:
                    print_hint(f'Unknown disposition: { disposition }\n')
                    exit(1)
            else:

                if "condition" in field:
                    condition_name = field["condition"]
                    if condition_name in conditions:
                        condition  = self.__gen_condition_from_field(conditions[condition_name][0])

			 # if condition variable is defined after condition, then create an enum.
			 #TODO: create check to ensure that union members are the same size!
                        idx_cond,  _ = self.__class_decl.member_vars[condition_name]
                        idx_field, _ = self.__class_decl.member_vars[name]

                        union_name = ""
                        if idx_cond > idx_field and len(conditions[condition_name]) > 1:
                                union_name = condition_name+"_union"
    
                        self.__deserializer.condition_field( name, var_type, condition, union_name )
                        self.__serializer.condition_field( name, var_type, condition, union_name )
                        self.__size_generator.condition( name, var_type, condition, union_name )
                        self.__print_generator.condition( name, var_type, condition, union_name )

                        del conditions[condition_name]

                else:
                    self.__deserializer.normal_field( var_type, name )
                    self.__serializer.normal_field( var_type, name )
                    self.__size_generator.normal_field( var_type, name )
                    self.__print_generator.normal_field( var_type, name, print_hint )



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
        self.__includes.add( "#include <iostream>" )
        self.__includes.add( "#include <iomanip>"  )
        self.__includes.add( "#include <limits>"   )
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

        condition_value = field["condition_value"]


        # if condition variable is an enum change to enum value 
        _, cond_type = self.__class_decl.member_vars[ field["condition"] ]
        if cond_type in self.__types.name_to_enum:
            condition_value = f'{cond_type}::{condition_value}'

        return f'{CppFieldGenerator.convert_to_field_name(field["condition"])} {op} {condition_value}'



