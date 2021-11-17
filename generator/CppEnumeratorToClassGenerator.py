import typing
import string

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
            type: TransactionType        # <--- note that 'TransactionType' is an enum class 
            value: MOSAIC_DEFINITION     # <--- note that 'MOSAIC_DEFINITION' is an enumerator in 'TransactionType' 
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


        # used for going from group_type group_version and group_id, to class name 
        # ( eg. class_name = type_to_versions_to_enum_to_classes[ decl.group_type ][decl.group_version][decl.group_id] )
        self.type_to_versions_to_enum_to_classes = { key: dict() for key in types_generator.name_to_enum.keys() } 


        # Go through class declarations and build 'type_to_versions_to_enum_to_classes' dict
        for class_name, decl in class_declarations.items():

            #TODO: this is just temporary, both group_type and group_version should always be defined 
            if decl.group_version and not decl.group_type:
                lookup_str      = class_name.rstrip(string.digits) # remove version number from end of class name
                ref_decl        = class_declarations[lookup_str]   # get class declaration
                decl.group_type = ref_decl.group_type              # copy its type
                decl.group_id   = ref_decl.group_id                # copy its id

            if not decl.group_type: # not all classes belong to an enum group
                continue
            
            if decl.group_type not in self.type_to_versions_to_enum_to_classes:
                print(f'Error: Const type "{decl.group_type}" not defined as an enum!\n')
                exit(1)

            versions_to_enum_to_classes = self.type_to_versions_to_enum_to_classes[ decl.group_type ]

            if decl.group_version not in versions_to_enum_to_classes:
                versions_to_enum_to_classes[ decl.group_version ] = {}

            enum_to_classes = versions_to_enum_to_classes[ decl.group_version ]
            if decl.group_id in versions_to_enum_to_classes[ decl.group_version ]:
                print(f'Error: Same enum "{decl.group_type}"::"{decl.group_id}" used for multiple classes: "{class_name}" and "{enum_to_classes[decl.group_id]}"!\n')
                exit(1)

            self.type_to_versions_to_enum_to_classes[decl.group_type][decl.group_version][decl.group_id] = class_name

        # generate code output
        self.__generate_declaration_code()
        self.__generate_definition_code()
        self.__generate_includes()


    def __generate_definition_code( self ):

        for enum_class, versions_to_enum_to_classes in self.type_to_versions_to_enum_to_classes.items():
            if not versions_to_enum_to_classes:
                continue

            version_to_function_code  = f'std::unique_ptr<ICatbuffer> create_type_{enum_class}( {enum_class} type, size_t version )\n{{\n\t'
            version_to_function_code += f'switch( version )\n\t{{\n'

            for version, enum_to_classes in versions_to_enum_to_classes.items():

                version_to_function_code      += f'\t\tcase {version} : {{ return create_type_{enum_class}_v{version}( type ); }}\n'
                self.__definition_code_output += f'std::unique_ptr<ICatbuffer> create_type_{enum_class}_v{version}( {enum_class} type )\n{{\n\t'
                self.__definition_code_output += f'switch( type )\n\t{{\n'

                for enum_type, class_name in enum_to_classes.items():
                    self.__includes.add(f'#include "{class_name}.h"')
                    self.__definition_code_output += f'\t\tcase {enum_class}::{enum_type} : {{ return std::unique_ptr<ICatbuffer>( new {class_name}() ); }}\n'

                self.__definition_code_output += f'\n\t\tdefault: {{ printf("Error: Unknown {enum_class} type 0x%X\\n", (uint32_t) type); exit(1); }}\n\t}}\n}}\n\n'

            version_to_function_code += f'\n\t\tdefault: {{ printf("Error: Unknown {enum_class} type 0x%X with version: %lu\\n", (uint32_t) type, version); exit(1); }}\n\t}}\n}}\n\n'
            self.__definition_code_output += version_to_function_code


    def __generate_declaration_code( self ):

        for enum_class, version_to_types in self.type_to_versions_to_enum_to_classes.items():

            if not version_to_types:
                continue

            self.__declaration_code_output += f'std::unique_ptr<ICatbuffer> create_type_{enum_class}( {enum_class} type, size_t version );\n'



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