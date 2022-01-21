

class TypeConverter():

    @staticmethod
    def convert( type: str ) -> str:
        yaml_types = {'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64'}

        if type in yaml_types:
            return type+"_t"
        else:
            return type



class CppFieldGenerator():
    builtin_types = {'int8_t', 'uint8_t', 'int16_t', 'uint16_t', 'int32_t', 'uint32_t', 'int64_t', 'uint64_t'}


    @staticmethod
    def convert_to_field_name( name: str ):
        """
        Converts field name to class member name
        """
        if name:
            name = 'm' + name[:1].upper() + name[1:]
        return name


    @staticmethod
    def gen_inline_field( type: str, comments: str = "" ):
        """
        Takes a field dict like the one below:

            ----------------------
            - comments: ''
              disposition: inline
              type: Transaction
            ----------------------

        and converts it to:

            -------------------------
         	Transaction mTransaction;
            -------------------------
        """

        return CppFieldGenerator.gen_normal_field( type, type, comments )


    @staticmethod
    def gen_const_field( type: str, name: str, value: int, comment: str = "" ) -> str:
        """
        Takes a field dict like the one below:

            ----------------------------
            - comments: ''
              name: TRANSACTION_VERSION
              type: const 'uint8'
              value: 1
            ----------------------------

        and converts it to:

            ---------------------------------------
            const uint8_t mTRANSACTION_VERSION = 1;
            ---------------------------------------

        """
        # Will be converted to either:
        #   - MyEnumType name = MyEnumType::value; (if type is in builtin_types)
        # or
        #   - uint32_t name = value; (if type is not in builtin_types)
        #

        name    = CppFieldGenerator.convert_to_field_name( name )
        value   = f'{type}::{value}' if type not in CppFieldGenerator.builtin_types else value
        output  = f'\tconst {type} {name} = {value};' 
        output += f'//< {comment}\n' if comment else "\n"
        return output


    @staticmethod
    def gen_reserved_field( type: str, name: str, size: int = 0, comment: str = "" ) -> str:
        """
        Takes a field dict like the one below:

            -------------------------------------------------------------------
            - comments: reserved padding to align next field on 8-byte boundary
              name: padding
              type: reserved uint32
              value: 0
            -------------------------------------------------------------------
        
        and converts it to:

            ------------------------------------------------------------------------------
        	uint32_t mPadding; //< reserved padding to align next field on 8-byte boundary
            ------------------------------------------------------------------------------
        """

        return CppFieldGenerator.gen_normal_field( type, name, size, comment )


    @staticmethod
    def gen_normal_field( type: str, name: str, size: int = 0, comments: str = "") -> str:
        """
        Takes a field dict like the ones below:

            -------------------------    
            - comments: mosaic nonce    
              name: nonce               
              type: MosaicNonce         
            -------------------------   
                                        
        and converts it to:             

            -------------------         
            MosaicNonce mNonce;         
            -------------------            

        or :
             - uint8_t name[size];' (if 'type' is byte) 

             - uint32_t name; (if 'type' is in 'builtin_types')
        """

        name   = CppFieldGenerator.convert_to_field_name( name )
        output = ""

        if( "byte" == type ):
            output = f'\tuint8_t {name}[{size}];'
        else:
            output = f'\t{type} {name};'

        output += f' // {comments}\n' if comments else "\n"
        return output


    @staticmethod
    def gen_array_field( type: str, name: str, comments: str = "") -> str:
        """
        Takes a field dict like the one below:

            -----------------------------------------
            - comments: cosignatory addresses
              disposition: array
              name: addresses
              size: addresses_count
              type: Address
            -----------------------------------------

        and converts it to:

            ---------------------------------------------------------------------------
            std::vector<UnresolvedAddress> mAddress_additions; // cosignatory addresses
            ---------------------------------------------------------------------------
        """
        
        name    = CppFieldGenerator.convert_to_field_name( name )
        output  = f'\tstd::vector<{type}> {name};'
        output += f' // {comments}\n' if comments else "\n"
        return output


    @staticmethod
    def gen_array_sized_field( name: str, comment: str ):
        """
        TODO: explain this. transactions are variable sized and payload size is in bytes)

        Takes a field dict like the one below:

            --------------------------------
            - comments: sub-transaction data 
              name: transactions
              size: payload_size
              type: array_sized EmbeddedTransaction
              header_type_field: type
            --------------------------------

        and converts it to:

            -------------------------------------------------------------------------------
            std::vector<std::unique_ptr<ICatbuffer>> mTransactions; // sub-transaction data
            -------------------------------------------------------------------------------
        """

        return CppFieldGenerator.gen_array_field("std::unique_ptr<ICatbuffer>", name, comment)


    @staticmethod
    def gen_array_fill_field( type: str, name: str, comments: str = "" ) -> str:
        """
        Takes a field dict like the one below:

            -----------------------------------------------------------------------------
            - comments: cosignatures data (fills remaining body space after transactions)
              disposition: array fill
              name: signatures
              size: 0
              type: Cosignature
            -----------------------------------------------------------------------------

        and converts it to:

            -------------------------------------------------------------------------------------------------------------
            std::vector<Cosignature> mSignatures; //< cosignatures data (fills remaining body space after transactions)
            -------------------------------------------------------------------------------------------------------------
        """

        return CppFieldGenerator.gen_array_field( type, name, comments )


    # TODO: Should ideally disappear by changing the schemas
    @staticmethod
    def gen_condition_field( name: str, fields: dict, member_vars ):
        """
        TODO: DOCUMENT!!!
        """

        output = ""
        if len(fields) > 1 and name not in member_vars:
            output += f'\tunion\n\t{{\n'

        for field in fields:
            output += f'\t\t{field["type"]} {CppFieldGenerator.convert_to_field_name(field["name"])};'
            
            if "comments" in field:
                output += f'// {field["comments"]}'
                
            output += '\n'

        if len(fields) > 1 and name not in member_vars:
            output += f'\t}} {CppFieldGenerator.convert_to_field_name(name)}_union;\n\n'

        return output
