import unittest
from generator.CppClassDeclarationGenerator import CppClassDeclarationGenerator, YamlFieldCheckResult
from generator.YamlFieldChecker import YamlFieldCheckResult
from generator.CppTypesGenerator import CppTypesGenerator

# [{'comments': 'entity version', 'name': 'version', 'signedness': 'unsigned', 'size': 2, 'type': 'uint16_t'}, {'comments': 'entity network', 'name': 'network', 'type': 'NetworkType'}, {'comments': 'entity timestamp', 'name': 'timestamp', 'type': 'Timestamp'}, 
        
# {'comments': 'entity signer public key size', 'disposition': 'reserved', 'name': 'signer_public_key_size', 'signedness': 'unsigned', 'size': 4, 'type': 'byte', 'value': 32}, {'comments': 'entity signer public key', 'name': 'signer_public_key', 'type': 'PublicKey'}, {'comments': 'entity signature size', 'disposition': 'reserved', 'name': 'signature_size', 'signedness': 'unsigned', 'size': 4, 'type': 'byte', 'value': 64}, {'comments': 'entity signature', 'name': 'signature', 'type': 'Signature'}]

#    def test_upper(self):
#        self.assertEqual('foo'.upper(), 'FOO')
#
#    def test_isupper(self):
#        self.assertTrue('FOO'.isupper())
#        self.assertFalse('Foo'.isupper())
#
#    def test_split(self):
#        s = 'hello world'
#        self.assertEqual(s.split(), ['hello', 'world'])
#        # check that s.split fails when the separator is not a string
#        with self.assertRaises(TypeError):
#            s.split(2)


class TestYamlFieldErrorDetection( unittest.TestCase ):

    def check( self, fields: list, pass_result: YamlFieldCheckResult ):

        types = CppTypesGenerator()
        types.name_to_enum["DummyEnum"] = set()
        types.name_to_enum["DummyEnum"].add("DummyEnumValue")

        decl = CppClassDeclarationGenerator()
        result, error_str = decl.init( "TestStruct", fields, types, set({"DummyClass"}) )

        #print( error_str )
        self.assertEqual( result, pass_result )


    # TODO: rewrite when disposition key is deprecated 
    def test_invalid_disposition_is_detected(self):
        fields = [{ 'name'        : 'test_var',
                    'type'        : 'uint8',
                    'disposition' : 'invalid_disposition' }]

        self.check(fields, YamlFieldCheckResult.DISPOSITION_INVALID)


    def test_missing_type_is_detected(self):
        fields = [{ 'name': 'test_var' }]

        self.check( fields, YamlFieldCheckResult.TYPE_MISSING )


    def test_missing_name_is_detected(self):
        fields = [{ 'type': 'byte', 'size': 1, 'signedness': 'signed' }]

        self.check( fields, YamlFieldCheckResult.NAME_MISSING )


    def test_undefined_type_is_detected(self):
        fields = [{ 'name': 'test_var',
                    'type': 'invalid_type' }]

        self.check( fields, YamlFieldCheckResult.TYPE_UNKNOWN )


    def test_field_name_redeclaration_is_detected(self):
        fields = [{ 'name': 'test_var',
                    'type': 'DummyClass' },

                  { 'name': 'test_var',
                    'type': 'DummyClass' }]

        self.check( fields, YamlFieldCheckResult.NAME_REDEFINED )


    # condition tests
    # /////////////////////////////////////////////////////////////////
    def test_undefined_conditional_operator_detected(self):
        fields = [{ 
                    'name': 'test_var',
                    'type': 'DummyClass',
                    'condition': 'cond_var',
                    #'condition_operation': 'equals',
                    'condition_value': '0' 
                  }]

        self.check( fields, YamlFieldCheckResult.CONDITION_OP_MISSING )

    def test_missing_conditional_operator_detected(self):
        fields = [{ 
                    'name': 'test_var',
                    'type': 'DummyClass',
                    'condition': 'cond_var',
                    'condition_operation': 'invalid op',
                    'condition_value': '0' 
                  }]

        self.check( fields, YamlFieldCheckResult.CONDITION_OP_UNKNOWN )
        
    def test_missing_condition_value_detected(self):
        fields = [{ 
                    'name': 'test_var',
                    'type': 'DummyClass',
                    'condition': 'cond_var',
                    'condition_operation': 'equals',
                    #'condition_value': '0'
                  }]

        self.check( fields, YamlFieldCheckResult.CONDITION_VALUE_MISSING )

    # TODO: disabled for now, enable when adding Enums
    def disable_test_undefined_condition_var_detected(self):
        fields = [{ 
                    'name': 'test_var',
                    'type': 'DummyClass',
                    'condition': 'cond_var',
                    'condition_operation': 'equals',
                    'condition_value': '0' 
                  }]

        self.check( fields, YamlFieldCheckResult.CONDITION_VAR_NOT_DEFINED )
    # /////////////////////////////////////////////////////////////////




    # reserved tests
    # /////////////////////////////////////////////////////////////////
    def test_reserved_missing_value_detected(self):
        fields = [{
                   'name'       : 'padding',
                   'type'       : 'uint32',
                   #'value'      : '0',
                   'disposition': 'reserved',
                 }]

        self.check( fields, YamlFieldCheckResult.VALUE_MISSING )

    def test_reserved_value_not_numeric_detected(self):
        fields = [{
                   'name'       : 'padding',
                   'type'       : 'uint32',
                   'value'      : 'a',
                   'disposition': 'reserved',
                 }]

        self.check( fields, YamlFieldCheckResult.VALUE_NOT_NUMERIC_NOR_ENUM )
    # /////////////////////////////////////////////////////////////////


    # inline tests
    # /////////////////////////////////////////////////////////////////
    def test_inline_missing_type_detected(self):
        fields = [{
                   #'type'       : 'uint32',
                   'disposition': 'inline',
                 }]

        self.check( fields, YamlFieldCheckResult.TYPE_MISSING )


    def test_inline_unknown_type_detected(self):
        fields = [{
                   'type'       : 'UnknownType',
                   'disposition': 'inline',
                 }]

        self.check( fields, YamlFieldCheckResult.TYPE_UNKNOWN )
    # /////////////////////////////////////////////////////////////////


    # const tests
    # /////////////////////////////////////////////////////////////////
    def test_const_unknown_type_detected(self):
        fields = [{
                   'name'       : 'VERSION',
                   'type'       : 'UnknownType',
                   'value'      : '123',
                   'disposition': 'const',
                 }]

        self.check( fields, YamlFieldCheckResult.VALUE_AND_TYPE_MISMATCH )

    def test_const_unknown_type_detected(self):
        fields = [{
                   'name'       : 'VERSION',
                   'type'       : 'UnknownType',
                   'value'      : 'UnknownEnum',
                   'disposition': 'const',
                 }]

        self.check( fields, YamlFieldCheckResult.TYPE_UNKNOWN )

    def test_const_unknown_enum_detected(self):
        fields = [{
                   'name'       : 'VERSION',
                   'type'       : 'DummyEnum',
                   'value'      : 'UnknownEnumValue',
                   'disposition': 'const',
                 }]

        self.check( fields, YamlFieldCheckResult.VALUE_NOT_NUMERIC_NOR_ENUM )
    # /////////////////////////////////////////////////////////////////


    # array tests
    # /////////////////////////////////////////////////////////////////
    def test_array_size_var_missing_detected(self):

        fields = [{
                    'name':        'test_array',
                    #'size':        'undefined_var',
                    'disposition': 'array',
                    'type':        'uint64',
                 }]
        self.check( fields, YamlFieldCheckResult.ARRAY_SIZE_MISSING )

    def test_array_size_var_unknown_detected(self):

        fields = [
                  #{
                  #  'name' : 'undefined_var',
                  #  'type' : 'byte', 'size': 1, 'signedness': 'signed'
                  #},
                  {
                    'name':        'test_array',
                    'size':        'undefined_var',
                    'disposition': 'array',
                    'type':        'uint64',
                  }
                 ]
        self.check( fields, YamlFieldCheckResult.ARRAY_SIZE_UNKNOWN )

    def test_array_size_var_not_builtin(self):

        fields = [
                  {
                    'name' : 'NoneIntVar',
                    'type' : 'DummyClass'
                  },
                  {
                    'name':        'test_array',
                    'size':        'NoneIntVar',
                    'disposition': 'array',
                    'type':        'uint64',
                  }
                 ]
        self.check( fields, YamlFieldCheckResult.ARRAY_SIZE_VAR_NOT_BUILTIN_TYPE )

#    def test_array_size_var_defined_after_array_detected(self):
#
#        fields = [
#                  {
#                    'name':        'test_array',
#                    'size':        'post_var',
#                    'disposition': 'array',
#                    'type':        'uint64',
#                  },
#                  {
#                    'name': 'post_var',
#                    'type': 'byte', 'size': 1, 'signedness': 'signed'
#                  }
#                 ]
#        self.check( fields, DeclGenResult.ARRAY_SIZE_VAR_DEFINED_AFTER )

    # /////////////////////////////////////////////////////////////////


    # array_sized tests
    # /////////////////////////////////////////////////////////////////
    def test_array_sized_missing_header_detected(self):
        fields = [{ 'name'             : 'transactions',
                    'disposition'      : 'array sized',
                    'size'             : 'payload_size',
                    'type'             : 'EmbeddedTransaction',
                    #'header'           : 'EmbeddedTransaction',
                    'header_type_field': 'elem_type' 
                  }]

        self.check( fields, YamlFieldCheckResult.ARRAY_SIZED_HEADER_MISSING )


    def test_array_sized_missing_header_type_detected(self):
        fields = [{ 'name'             : 'transactions',
                    'disposition'      : 'array sized',
                    'size'             : 'payload_size',
                    'type'             : 'EmbeddedTransaction',
                    'header'           : 'EmbeddedTransaction',
                    #'header_type_field': 'elem_type' 
                 }]

        self.check( fields, YamlFieldCheckResult.ARRAY_SIZED_HEADER_TYPE_MISSING )


    def test_array_sized_missing_size(self):
        fields = [{ 'name'             : 'transactions',
                    'disposition'      : 'array sized',
                    #'size'             : 'payload_size',
                    'type'             : 'EmbeddedTransaction',
                    'header'           : 'EmbeddedTransaction',
                    'header_type_field': 'elem_type' 
                 }]

        self.check( fields, YamlFieldCheckResult.ARRAY_SIZE_MISSING )


    # /////////////////////////////////////////////////////////////////


    # array_fill tests
    # /////////////////////////////////////////////////////////////////
    def test_array_fill_type_unknown(self):

        fields = [
                  {
                    'name':        'array_fill_test',
                    'disposition': 'array fill',
                    'type':        'UnknownType',
                  }
                 ]
        self.check( fields, YamlFieldCheckResult.TYPE_UNKNOWN )


    # /////////////////////////////////////////////////////////////////






if __name__ == '__main__':
    unittest.main()


#value ="a"
#a = ['a','b','c']
#b = ['d','e','f']
#d = ['g','a','i']
#c = ['j','k','l']
#
#any([True for x in [a,b,c,d] if value in x])
#
#
#[x for x in [a,b,c,d] if value in x]
#
#
#print( value in a,b,c,d )
#
#any(value in lists for lists in [a,b,c,d]):
#
#any(subdir in path_elements for subdir in ['int', 'bench', 'stress']):
