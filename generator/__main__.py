import yaml
import shutil
from pathlib import Path
import sys
from distutils.dir_util import copy_tree

from .CppClassDefinitionGenerator import CppClassDefinitionGenerator
from .CppClassDeclarationGenerator import CppClassDeclarationGenerator
from .CppTypesGenerator import CppTypesGenerator
from .CppEnumeratorToClassGenerator import CppEnumeratorToClassGenerator


def main():
    """
    Takes a .yaml file and generates C++ code in an output folder.

    Command line: 'python3 -m generator myYamlFile.yaml MyOutputFolder'

    The steps taken are: 

        1) Generate enum and user defined types in 'types.h'
        2) Generate class declarations (*.h) for complex types
        3) Generate class definitions (*.cpp) for complex types
        4) Generate 'enum to class' converters in file 'converters.h'
    """

    # Check if enough arguments
    if len(sys.argv) < 3:
        print( "Error: Not enough command line arguments!\n" )
        exit(1)


    # Check if .yaml input file exists
    input_file_name = sys.argv[1]

    my_file = Path(input_file_name)
    if not my_file.is_file():
        print(f"Error: File '{input_file_name}' not found!\n")
        exit(1)


    # Create output folder
    output_folder = sys.argv[2]
    print("Output folder:", output_folder)
    Path( output_folder ).mkdir( parents=True, exist_ok=True )

    gen_output_folder = output_folder+"/generated_src"
    dirpath = Path(gen_output_folder)
    
    if dirpath.exists() and dirpath.is_dir():
        shutil.rmtree( gen_output_folder )

    Path( gen_output_folder ).mkdir( parents=True, exist_ok=True )

    copy_tree("cpp_source", output_folder+"/static_src")
    shutil.copy("cpp_build_files/CMakeLists.txt", output_folder+"/")


    # Read YAML file
    with open(input_file_name, 'r') as stream:
        data_loaded = yaml.safe_load(stream)


    # Generate enum types
    types_generator = CppTypesGenerator()
    for elem in data_loaded:
        if 'enum' == elem['type']: 
            types_generator.add_enum_type( elem )


    # Generate user defined types
    for elem in data_loaded:
        if 'byte' == elem['type']:
            types_generator.add_user_type( elem )

    types_generator.write_file(gen_output_folder+"/types.h")


    # Generate class declarations (*.h)
    name_to_class = {}
    for elem in data_loaded:
        if 'struct'== elem['type']:

            # Generate class declaration
            class_name    = elem['name']
            class_dec_gen = CppClassDeclarationGenerator(class_name, elem['layout'], types_generator)
            class_dec_gen.write_file( gen_output_folder+f'/{class_name}.h' )

            name_to_class[elem['name']] = class_dec_gen


    # Generate class definitions (*.cpp)
    for elem in data_loaded:
        if 'struct' == elem['type']:
            class_decl     = name_to_class[elem['name']]
            class_impl_gen = CppClassDefinitionGenerator( class_decl, name_to_class, types_generator )
            class_impl_gen.write_file( gen_output_folder+f'/{class_decl.class_name}.cpp' )


    # Generate enum to class converters
    converter = CppEnumeratorToClassGenerator( name_to_class, types_generator )
    converter.write_file( gen_output_folder )

    print("Done!")



if __name__ == "__main__":
    main()










# Why have disposition=reserved? makes no difference, just keep it as byte
# condition_value: ROOT --> define where root comes from? from enum? what if multiple enums contain root, which one should we choose



