import typing
import yaml
import shutil
from pathlib import Path
import sys
from distutils.dir_util import copy_tree

from .CppClassDefinitionGenerator import CppClassDefinitionGenerator
from .CppClassDeclarationGenerator import CppClassDeclarationGenerator 
from .YamlFieldChecker import YamlFieldCheckResult
from .CppTypesGenerator import CppTypesGenerator
from .CppConvertersGenerator import CppConvertersGenerator


def generate( input_data: list, gen_output_folder: str, generate_print_methods: bool = False):

    # Generate enum types
    print("Generating enum types:")
    class_decls : typing.Dict[str, CppClassDeclarationGenerator] = {}
    types_generator = CppTypesGenerator()
    for elem in input_data:
        elem_type = elem['type'].split()
        if 'enum' == elem_type[0]: 
            types_generator.add_enum_type( elem )
            print("\t"+elem["name"])
        elif 'struct' == elem['type']:
            class_decls[elem['name']] = CppClassDeclarationGenerator()

    # Generate alias types
    print("\nGenerating alias types:")
    for elem in input_data:
        elem_type = elem['type'].split()
        if 'alias' == elem_type[0]:
            types_generator.add_alias_type( elem )
            print("\t"+elem["name"])

    types_generator.write_file(gen_output_folder+"/types.h")


    # Generate class declarations (*.h)
    print("\nGenerating class declarations:")
    for elem in input_data:
        if 'struct'== elem['type']:

            # Generate class declaration
            comments           = elem['comments'] if "comments" in elem else ""
            class_name         = elem['name']
            class_dec_gen      = class_decls[class_name]
            result, result_str = class_dec_gen.init(class_name, elem['layout'], types_generator, class_decls, comments, generate_print_methods)

            if result != YamlFieldCheckResult.OK:
                print(result_str)
                exit(1)

            class_dec_gen.write_file( gen_output_folder+f'/{class_name}.h' )

            class_decls[elem['name']] = class_dec_gen
            print("\t"+elem["name"])


    for class_name, decl in class_decls.items():
        decl.check_dependency()

    # Generate class definitions (*.cpp)
    print("\nGenerating class definitions:")
    for elem in input_data:
        if 'struct' == elem['type']:
            print("\t"+elem["name"])

            class_decl         = class_decls[elem['name']]
            class_def_gen      = CppClassDefinitionGenerator()
            class_def_gen.init( class_decl, class_decls, types_generator, generate_print_methods )

            class_def_gen.write_file( gen_output_folder+f'/{class_decl.class_name}.cpp' )


    # Generate enum to class converters
    converter = CppConvertersGenerator( class_decls, types_generator, generate_print_methods )
    converter.write_file( gen_output_folder )

    print("\nDone!")






def main():
    """
    Takes a .yaml file and generates C++ code in an output folder.

    Command line: 'python3 -m generator myYamlFile.yaml MyOutputFolder'

    The steps taken are: 

        1) Generate enum and aliases in 'types.h'
        2) Generate class declarations (*.h) for struct types
        3) Generate class definitions (*.cpp) for struct types
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
    print(f"Creating output folder:{output_folder}\n")
    Path( output_folder ).mkdir( parents=True, exist_ok=True )

    gen_output_folder = output_folder+"/generated_src"
    dirpath = Path(gen_output_folder)
    
    if dirpath.exists() and dirpath.is_dir():
        shutil.rmtree( gen_output_folder )

    Path( gen_output_folder ).mkdir( parents=True, exist_ok=True )


    # Copy static files
    copy_tree("cpp_source", output_folder+"/static_src")


    # Generate pretty print or not
    generate_print_methods = False

    if len(sys.argv) == 4:
       if( sys.argv[3] == "--generate-print" ):
           generate_print_methods = True
       else:
           print(f"Error: unknown argument '{sys.argv[3]}'")
           exit(1)


    # Copy build file
    if not generate_print_methods:
        file = Path(output_folder+"/static_src/cmd.cpp")
        file.unlink()
        file = Path(output_folder+"/static_src/ICatbufferPrint.h")
        file.unlink()
        file = Path(output_folder+"/static_src/IPrettyPrinter.h")
        file.unlink()

        shutil.copy("cpp_build_files/CMakeLists.txt", output_folder+"/")
    else:
        shutil.move(output_folder+"/static_src/ICatbufferPrint.h", output_folder+"/static_src/ICatbuffer.h")
        shutil.copy("cpp_build_files/CMakeLists_with_cmd.txt", output_folder+"/CMakeLists.txt")


    # Read YAML file
    print(f"Reading YAML file: {input_file_name}\n")
    with open(input_file_name, 'r') as stream:
        data_loaded = yaml.safe_load(stream)

    generate( data_loaded, gen_output_folder, generate_print_methods)



if __name__ == "__main__":
    main()
