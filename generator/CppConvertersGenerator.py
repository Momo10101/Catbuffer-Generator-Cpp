import typing
import string

from .CppClassDeclarationGenerator import CppClassDeclarationGenerator
from .CppTypesGenerator import CppTypesGenerator
from .CppFieldGenerator import CppFieldGenerator



class CppConvertersGenerator():
    """
    Generates functions which convert a type enumerator, RawBuffer or buffer
    name, to an ICatbuffer class. The link between an enumerator and a class 
    is done via the 'group_type' and 'group_id' variables in 'CppClassDeclarationGenerator'.

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

    For example, if the above function is called like so:
    
        ------------------------------------------------------------------
        create_type_TransactionType( TransactionType::MOSAIC_DEFINITION );
        ------------------------------------------------------------------
    
    then a 'MosaicDefinition' object is returned as an ICatbuffer pointer, which can be
    used to serialize and deserialize raw binary data containing the MosaicDefinition fields.

    All converters are declared in 'converters.h' and implemented in 'converters.cpp'.
    """

    def __init__( self,
                  class_declarations:     typing.Dict[str, CppClassDeclarationGenerator],
                  types_generator:        CppTypesGenerator,
                  generate_print_methods: bool = False) -> None:

        self.__includes: typing.Set[str] = set()
        self.__include_code_output       = ""
        self.__declaration_code_output   = ""
        self.__definition_code_output    = ""
        self.__generate_print_methods    = generate_print_methods

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
        self.__generate_declarations()
        self.__generate_enum_type_to_class_methods()

        if generate_print_methods:
            self.__generate_string_to_class_method( class_declarations )
            self.__generate_rawbuffer_to_class_methods( class_declarations )
            self.__generate_enum_group_to_class_methods()

        self.__generate_includes()


    def __generate_enum_type_to_class_methods( self ):

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

                self.__definition_code_output += f'\n\t\tdefault: {{ return nullptr; }}\n\t}}\n}}\n\n'

            version_to_function_code += f'\n\t\tdefault: {{ return nullptr; }}\n\t}}\n}}\n\n'
            self.__definition_code_output += version_to_function_code


    def __generate_declarations( self ):

        for enum_class, version_to_types in self.type_to_versions_to_enum_to_classes.items():

            if not version_to_types:
                continue

            self.__declaration_code_output += f'/**\n'
            self.__declaration_code_output += f" * Function to create an instance of a class belonging to the class group '{enum_class}'.\n"
            self.__declaration_code_output += f' * \n'
            self.__declaration_code_output += f" * @param[in] type     The class with enum-type 'type', which should be instantiated.\n"
            self.__declaration_code_output += f" * @param[in] version  The the version of the class which should be instantiated.\n"
            self.__declaration_code_output += f" * @return             nullptr if 'type' and 'version' does not correspond to a class, otherwise pointer to instantiated class.\n"
            self.__declaration_code_output += f' */\n'
            self.__declaration_code_output += f'std::unique_ptr<ICatbuffer> create_type_{enum_class}( {enum_class} type, size_t version );\n\n\n'

        if self.__generate_print_methods:
            self.__declaration_code_output += f'/**\n'
            self.__declaration_code_output += f" * Function to convert a RawBuffer to an instance of a class belonging to the class group 'group_name'.\n"
            self.__declaration_code_output += f" * The type of buffer is auto detected by looking at type and version fields in the buffer header.\n"
            self.__declaration_code_output += f' * \n'
            self.__declaration_code_output += f" * @param[in] inputBuf    The buffer which will be deserialized to create class instance.\n"
            self.__declaration_code_output += f" * @param[in] group_name  The name of the group which the buffer belongs to.\n"
            self.__declaration_code_output += f" * @return                nullptr if buffer does not correspond to a class, otherwise pointer to instantiated class.\n"
            self.__declaration_code_output += f' */\n'
            self.__declaration_code_output += f'std::unique_ptr<ICatbuffer> create_type( RawBuffer& inputBuf, std::string group_name );\n\n\n'
            
            self.__declaration_code_output += f'/**\n'
            self.__declaration_code_output += f" * Function to convert a buffer name to a class instance.\n"
            self.__declaration_code_output += f' * \n'
            self.__declaration_code_output += f" * @param[in] buffer_name  The name of the buffer which should be instantiated.\n"
            self.__declaration_code_output += f" * @return                 nullptr if name does not correspond to a class, otherwise pointer to instantiated class.\n"
            self.__declaration_code_output += f' */\n'
            self.__declaration_code_output += f'std::unique_ptr<ICatbuffer> create_type( std::string buffer_name );\n\n\n'


    def __generate_includes( self ):

        for include in self.__includes:
            self.__include_code_output += (include + "\n")

        self.__include_code_output += '\n'


    def __generate_string_to_class_method( self, class_declarations: typing.Dict[str, CppClassDeclarationGenerator] ):

        if 0 == len(class_declarations):
            return


        self.__definition_code_output += f'std::unique_ptr<ICatbuffer> create_type( std::string buffer_name )\n{{\n'

        class_names = list(class_declarations.keys())
        first_class = class_names[0]
        
        self.__definition_code_output += f'\tif("{first_class}" == buffer_name){{ return std::unique_ptr<ICatbuffer>( new {first_class}() ); }}\n'
        self.__includes.add(f'#include "{first_class}.h"')
        for class_name in class_names[1:]:
            self.__definition_code_output += f'\telse if("{class_name}" == buffer_name){{ return std::unique_ptr<ICatbuffer>( new {class_name}() ); }}\n'
            self.__includes.add(f'#include "{class_name}.h"')

        self.__definition_code_output += "\telse { return nullptr; }\n"
        self.__definition_code_output += "}\n\n"


    def __generate_enum_group_to_class_methods( self ):
        group_names = []

        for enum_class, versions_to_enum_to_classes in self.type_to_versions_to_enum_to_classes.items():
            if not versions_to_enum_to_classes:
                continue

            group_names.append(enum_class)

        self.__definition_code_output += f'std::unique_ptr<ICatbuffer> create_type( RawBuffer& inputBuf, std::string group_name )\n{{\n'
        if len(group_names) > 0:
            self.__definition_code_output += f'\tif( "{group_names[0]}" == group_name ){{ return create_type_{group_names[0]}( inputBuf ); }}\n'

            for group_name in group_names[1:]:
                self.__definition_code_output += f'\telse if( "{group_name}" == group_name ){{ return create_type_{group_name}( inputBuf ); }}\n'

            self.__definition_code_output += f'\telse\n\t{{\n'
            self.__definition_code_output += f'\t\tprintf( "Error: %s is not a valid buffer type!\\n", group_name.c_str() );\n'
            self.__definition_code_output += f'\t\texit(1);\n\t}}\n}}\n\n'
        else:
            self.__definition_code_output += f'\t(void) inputBuf;\n'
            self.__definition_code_output += f'\tprintf( "Error: Buffer type %s was not defined in the schemas!\\n", group_name.c_str() );\n'
            self.__definition_code_output += f'\texit(1);\n\n}}\n\n'


    def __generate_rawbuffer_to_class_methods( self, class_decls ):
        group_names = []

        for enum_class, versions_to_enum_to_classes in self.type_to_versions_to_enum_to_classes.items():
            if not versions_to_enum_to_classes:
                continue

            group_names.append(enum_class)

        for group_name in group_names:

            class_name    = list(self.type_to_versions_to_enum_to_classes[group_name]["1"].values())[0]
            header_class  = class_decls[class_name].group_header
            version_field = class_decls[class_name].header_version_field
            version_field = "header."+CppFieldGenerator.convert_to_field_name(version_field) if version_field else "1"

            self.__definition_code_output += f'std::unique_ptr<ICatbuffer> create_type_{group_name}( RawBuffer& inputBuf )\n'
            self.__definition_code_output += f'{{\n'
            self.__definition_code_output += f'  // Get header\n'
            self.__definition_code_output += f'  RawBuffer headerBuf = inputBuf;\n'
            self.__definition_code_output += f'  {header_class} header;\n'
            self.__definition_code_output += f'  bool succ = header.Deserialize( headerBuf );\n'
            self.__definition_code_output += f'\n'
            self.__definition_code_output += f'  if( !succ )\n'
            self.__definition_code_output += f'  {{\n'
            self.__definition_code_output += f'    header.Print(0);\n'
            self.__definition_code_output += f'    printf( "Error: Was not able to deserialize header! Error occurred at byte: %lu\\n", headerBuf.GetOffset() );\n'
            self.__definition_code_output += f'    return nullptr;\n'
            self.__definition_code_output += f'  }}\n'
            self.__definition_code_output += f'\n'
            self.__definition_code_output += f'  // Deserialize all of payload\n'
            self.__definition_code_output += f'  printf( "\\nDetected buffer of type 0x%X (%d) \\n\\n", (uint32_t) header.mType, (uint32_t) header.mType );\n'
            self.__definition_code_output += f'  std::unique_ptr<ICatbuffer> cat = create_type_{group_name}( header.mType, {version_field} );\n'
            self.__definition_code_output += f'  if( nullptr == cat )\n'
            self.__definition_code_output += f'  {{\n'
            self.__definition_code_output += f'    printf( "Error: Combination of type=%u and version=%u do not correspond to any buffer!\\n", (uint32_t) header.mType, {version_field} );\n'
            self.__definition_code_output += f'    return nullptr;\n'
            self.__definition_code_output += f'  }}\n'
            self.__definition_code_output += f'  succ = cat->Deserialize( inputBuf );\n'
            self.__definition_code_output += f'\n'
            self.__definition_code_output += f'  if( !succ )\n'
            self.__definition_code_output += f'  {{\n'
            self.__definition_code_output += f'    header.Print(0);\n'
            self.__definition_code_output += f'    printf( "Error: Was not able to deserialize header! Error occurred at byte: %lu\\n", headerBuf.GetOffset() );\n'
            self.__definition_code_output += f'    return nullptr;\n'
            self.__definition_code_output += f'  }}\n'
            self.__definition_code_output += f'\n'
            self.__definition_code_output += f'  return cat;\n'
            self.__definition_code_output += f'}}\n\n\n'

            self.__declaration_code_output += f'/**\n'
            self.__declaration_code_output += f" * Function to convert a RawBuffer to an instance of a class belonging '{group_name}'.\n"
            self.__declaration_code_output += f" * The type of buffer is auto detected by looking at type and version fields in the buffer header.\n"
            self.__declaration_code_output += f' * \n'
            self.__declaration_code_output += f" * @param[in] inputBuf    The buffer which will be deserialized to create class instance.\n"
            self.__declaration_code_output += f" * @return                nullptr if buffer does not correspond to a class belonging to '{group_name}', otherwise pointer to instantiated class.\n"
            self.__declaration_code_output += f' */\n'
            self.__declaration_code_output += f'std::unique_ptr<ICatbuffer> create_type_{group_name}( RawBuffer& inputBuf );\n\n\n'


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
