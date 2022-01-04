import unittest

from generator.CppTypesGenerator import CppTypesGenerator
from generator.CppClassDeclarationGenerator import CppClassDeclarationGenerator, YamlFieldCheckResult

from generator.YamlDependencyChecker import YamlDependencyCheckerResult

class TestYamlDependencyErrorDetection( unittest.TestCase ):

    # array_sized tests
    # /////////////////////////////////////////////////////////////////
    def test_array_sized_missing_type_field(self):
        fieldsA = [{
                    'name': 'elem_type',
                    'type': 'uint8'
                  }]

        fieldsB = [{
                    'name'             : 'transactions',
                    'size'             : 'payload_size',
                    'type'             : 'array_sized ClassA',
                    'header_type_field': 'elem'  # 'elem' does not exist, should be 'elem_type' and therefore should result in error
                  }]

        types            = CppTypesGenerator()
        declA            = CppClassDeclarationGenerator()
        declB            = CppClassDeclarationGenerator()
        class_decls      = { "ClassA" : declA, "ClassB" : declB }

        result, _ = declA.init( "ClassA", fieldsA, types, class_decls )
        result, _ = declB.init( "ClassB", fieldsB, types, class_decls )
        result, _ = declB.check_dependency()

        self.assertEqual( result, YamlDependencyCheckerResult.ARRAY_SIZED_TYPE_FIELD_NOT_DECLARED )


    def test_array_sized_unknown_header(self):
        fieldsA = [{
                    'name': 'elem_type',
                    'type': 'int8'
                  }]

        fieldsB = [{
                    'name'             : 'transactions',
                    'size'             : 'payload_size',
                    'type'             : 'array_sized ClassAA',
                    'header_type_field': 'elem_type' 
                  }]

        types            = CppTypesGenerator()
        declA            = CppClassDeclarationGenerator()
        declB            = CppClassDeclarationGenerator()
        class_decls      = { "ClassA" : declA, "ClassB" : declB }

        result, _ = declA.init( "ClassA", fieldsA, types, class_decls )
        result, _ = declB.init( "ClassB", fieldsB, types, class_decls )

        self.assertEqual( result, YamlFieldCheckResult.TYPE_UNKNOWN )



if __name__ == '__main__':
    unittest.main()

