import typing

from .CppClassDeclarationGenerator import CppClassDeclarationGenerator
from .CppTypesGenerator import CppTypesGenerator



class CppEnumeratorToClassGenerator():
    """
    Generates functions which convert a type enumerator to an ICatbuffer
    class. The link between an enumerator and a class is done via the 
    'group_type' and 'group_id' variables in 'CppClassDeclarationGenerator'.

    For example, given a struct defined as below:

        -----------------------------------
        - name: MosaicDefinition
          type: struct
          comments: ''
          layout:
          - comments: ''
            disposition: const
            name: TRANSACTION_TYPE
            type: TransactionType        (<--- note that 'TransactionType' is an enum class )
            value: MOSAIC_DEFINITION     (<--- note that 'MOSAIC_DEFINITION' is an enumerator in 'TransactionType' )
            .
            .
            .
        -----------------------------------

    a function like the one below is defined:

        -------------------------------------------------------------------------------
        std::unique_ptr<ICatbuffer> create_type_TransactionType( TransactionType type )
        -------------------------------------------------------------------------------

    If the above function is called like so:
    
        ------------------------------------------------------------------
        create_type_TransactionType( TransactionType::MOSAIC_DEFINITION ); 
        ------------------------------------------------------------------
    
    then a 'MosaicDefinition' object pointer is returned, which can be used to serialize and deserialize, 
    raw binary data containing the MosaicDefinition fields.

    All converters are declared in 'converters.h' and implemented in 'converters.cpp'.
    """

    def __init__( self,
                  class_declarations: typing.Dict[str, CppClassDeclarationGenerator],
                  types_generator:    CppTypesGenerator ) -> None:

        self.__includes: typing.Set[str] = set()
        self.__include_code_output       = ""
        self.__declaration_code_output   = ""
        self.__definition_code_output    = ""


        # used for going from group_type and group_id, to class name 
        # ( eg. class_name = type_to_enum_to_class[ decl.group_type ][decl.group_id] )
        self.type_to_enum_to_class = {key: dict() for key in types_generator.name_to_enum.keys() } 


        # Go through class declarations and build 'type_to_enum_to_class' dict
        for class_name, decl in class_declarations.items():

            if decl.group_type: # not all classes belong to an enum group

                if decl.group_type not in self.type_to_enum_to_class:
                    print(f'Error: Const type "{decl.group_type}" not defined as an enum!\n')
                    exit(1)

                enum_to_class = self.type_to_enum_to_class[ decl.group_type ]

                if decl.group_id in enum_to_class:
                    print(f'Error: Same enum "{decl.group_type}"::"{decl.group_id}" used for multiple classes: "{class_name}" and "{enum_to_class[decl.group_id]}"!\n')
                    exit(1)

                self.type_to_enum_to_class[ decl.group_type ][decl.group_id] = class_name


        # generate code output
        self.__generate_declaration_code()
        self.__generate_definition_code()
        self.__generate_includes()


    def __generate_definition_code( self ):

        for enum_class, types_to_models in self.type_to_enum_to_class.items():
            if not types_to_models:
                continue

            self.__definition_code_output += f'std::unique_ptr<ICatbuffer> create_type_{enum_class}( {enum_class} type )\n{{\n\t'
            self.__definition_code_output += f'switch(type)\n\t{{\n'

            for enum_type, model in types_to_models.items():
                self.__definition_code_output += f'\t\tcase {enum_class}::{enum_type} : {{ return std::unique_ptr<ICatbuffer>( new {model}() ); }}\n'
                self.__includes.add(f'#include "{model}.h"')

            self.__definition_code_output += f'\n\t\tdefault: {{ printf("Error: Unknown {enum_class} type 0x%X\\n", (uint32_t) type); exit(1); }}\n\t}}\n}}\n\n'


    def __generate_declaration_code( self ):

        for enum_class, types_to_models in self.type_to_enum_to_class.items():
            if not types_to_models:
                continue

            self.__declaration_code_output += f'std::unique_ptr<ICatbuffer> create_type_{enum_class}( {enum_class} type );\n'



    def __generate_includes( self ):

        for include in self.__includes:
            self.__include_code_output += (include + "\n")

        self.__include_code_output += '\n'


    def write_file( self, file_path: str ):
        """
        Writes generated code to converters.h/.cpp
        """

        f = open(file_path+f'/converters.h', "w")
        f.write("#pragma once\n\n")
        f.write("#include <memory>\n")
        f.write('#include "ICatbuffer.h"\n')
        f.write('#include "types.h"\n\n')
        f.write(self.__declaration_code_output)
        f.close()

        f = open(file_path+f'/converters.cpp', "w")
        f.write("#include <stdio.h>\n")
        f.write('#include "converters.h"\n\n')
        f.write(self.__include_code_output)
        f.write(self.__definition_code_output)
        f.close()