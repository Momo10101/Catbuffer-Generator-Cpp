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
    bool succ = transaction.Deserialize( header );

    if( !succ )
    {
      printf("Error: Was not able to deserialize header!\n");
      return 1;
    }


    // Deserialize all of payload
    printf("Test vector %lu\t | type 0x%X (%d) | ", i, (uint32_t) transaction.mType, (uint32_t) transaction.mType);
    std::unique_ptr<ICatbuffer> cat = create_type_TransactionType( transaction.mType, transaction.mEntityBody.mVersion );
    if( nullptr == cat )
    {
      printf("Error: Combination of type=%u and version=%u do not correspond to any class!\n", (uint32_t)transaction.mType, transaction.mEntityBody.mVersion);
      return 1;
    }
    succ = cat->Deserialize( inputBuf );

    if(!succ)
    {
      printf("Error: Was not able to deserialize data!:\n%s\n", payloads[i].c_str());
      return 1;
    }


    // Serialize
   	output.resize( input.size() );
    RawBuffer outputBuf( output.data(), output.size() );
    succ = cat->Serialize( outputBuf );

    if(!succ)
    {
      printf("Error: Was not able to serialize data\n");
      return 1;
    }


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

      return 1;
    }

  }

  printf("\nAll tests passed!\n\n");
  return 0;
}


