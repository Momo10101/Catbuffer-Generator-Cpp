#include <fstream>
#include <vector>

#include "converters.h"
#include "Transaction.h"

std::vector<uint8_t> HexToBytes(const std::string& hex) {
  std::vector<uint8_t> bytes;

  for (unsigned int i = 0; i < hex.length(); i += 2)
  {
    std::string byteString = hex.substr(i, 2);
    uint8_t byte = (uint8_t) strtol(byteString.c_str(), NULL, 16);
    bytes.push_back(byte);
  }

  return bytes;
}

 
int main( int argc, char* argv[] )
{
  std::string data;
  std::vector<uint8_t> input;
  std::vector<uint8_t> output;

  #include "payloads.h"
  
  for( size_t i=0; i<sizeof(payloads)/sizeof(std::string); ++i )
  {
    // create buffer
    input = HexToBytes( payloads[i] );
    RawBuffer inputBuf( input.data(), input.size() );


    // Get header
    RawBuffer header = inputBuf;
    Transaction transaction;
    transaction.Deserialize( header );


    // Deserialize all of payload
    printf("Test vector %lu | type %d | ", i, (int) transaction.mType);
    std::unique_ptr<ICatbuffer> cat = create_type_TransactionType( transaction.mType, transaction.mEntityBody.mVersion );
    cat->Deserialize( inputBuf );


    // Serialize
   	output.resize( input.size() );
    RawBuffer outputBuf( output.data(), output.size() );
    cat->Serialize( outputBuf );



    // compare results
    const bool testPassed = (output == input);
    printf("passed = %d\n", testPassed );

    if( !testPassed )
    {
      for( size_t i=0; i<output.size(); ++i )
      {
        if( output[i] != input[i] )
        {
          printf("\nFail at %lu !! (%u) != (%u)\n", i, output[i], input[i]);
          break;
        }
      }

      exit(1);
    }

  }

  printf("\nAll tests passed!\n\n");

}


