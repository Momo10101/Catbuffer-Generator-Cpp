import unittest

from generator.CppTypesGenerator import CppTypesGenerator
from generator.CppClassDeclarationGenerator import CppClassDeclarationGenerator, YamlFieldCheckResult

from generator.YamlDependencyChecker import YamlDependencyCheckerResult

class TestYamlDependencyErrorDetection( unittest.TestCase ):

    # array_sized tests
    # /////////////////////////////////////////////////////////////////
    def test_array_sized_missing_type_field(self):
        fieldsA = [{
                    'name' : 'elem_type',
                    'type': 'byte', 'size': 1, 'signedness': 'signed'
                  }]

        fieldsB = [{'name'             : 'transactions',
                    'disposition'      : 'array sized',
                    'size'             : 'payload_size',
                    'type'             : 'ClassA',
                    'header'           : 'ClassA',
                    'header_type_field': 'elem' 
                  }]


        types            = CppTypesGenerator()
        declA            = CppClassDeclarationGenerator()
        declB            = CppClassDeclarationGenerator()
        class_decls      = { "ClassA" : declA, "ClassB" : declB }

        result, error_str = declA.init( "ClassA", fieldsA, types, class_decls )
        result, error_str = declB.init( "ClassB", fieldsB, types, class_decls )
        result, error_str = declB.check_dependency()

        self.assertEqual( result, YamlDependencyCheckerResult.ARRAY_SIZED_TYPE_FIELD_NOT_DECLARED )


    def test_array_sized_unknown_header(self):
        fieldsA = [{
                    'name' : 'elem_type',
                    'type': 'byte', 'size': 1, 'signedness': 'signed'
                  }]

        fieldsB = [{
                    'name'             : 'transactions',
                    'disposition'      : 'array sized',
                    'size'             : 'payload_size',
                    'type'             : 'ClassAA',
                    'header'           : 'ClassAA',
                    'header_type_field': 'elem_type' 
                  }]


        types            = CppTypesGenerator()
        declA            = CppClassDeclarationGenerator()
        declB            = CppClassDeclarationGenerator()
        class_decls      = { "ClassA" : declA, "ClassB" : declB }

        result, error_str = declA.init( "ClassA", fieldsA, types, class_decls )
        result, error_str = declB.init( "ClassB", fieldsB, types, class_decls )
        result, error_str = declB.check_dependency()

        self.assertEqual( result, YamlDependencyCheckerResult.ARRAY_SIZED_HEADER_NOT_DECLARED )



if __name__ == '__main__':
    unittest.main()

