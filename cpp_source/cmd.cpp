#include <fstream>
#include <vector>
#include <string>
#include <iterator>

#include "../generated_src/converters.h"


std::vector<uint8_t> HexToBytes( const std::string& hex )
{
  std::vector<uint8_t> bytes;

  for( unsigned int i = 0; i < hex.length(); i += 2 )
  {
    std::string byteString = hex.substr(i, 2);
    uint8_t byte = (uint8_t) strtol(byteString.c_str(), NULL, 16);
    bytes.push_back(byte);
  }

  return bytes;
}


int main( int argc, char* argv[] )
{
  if( argc == 1 )
  {
    printf("Too few arguments!\n");

    return 0;
  }

  std::string cmd( argv[1] );

  if( cmd == "--help" )
  {
    printf( "Usage: cmd [options] file/hex...\n" );
    printf( "Options:\n" );
    printf( "  --help                      Display this information.\n");

    printf( "  --hex {buffer name}         Deserialize a hex string representing a {buffer name} catbuffer.\n");
    printf( "  --hex-auto {group type}     Deserialize a hex string representing a catbuffer belonging to {group type}\n");
    printf( "                              by automatically detecting the buffer type.\n\n");

    printf( "  --raw {header name}         Deserialize a raw file representing a {buffer name} catbuffer.\n");
    printf( "  --raw-auto {buffer type}    Deserialize a hex string representing a catbuffer belonging to {group type}\n");
    printf( "                              by automatically detecting the buffer type.\n\n");

    return 0;
  }
  else if( cmd == "--hex-auto" || cmd == "--hex" || cmd == "--raw-auto" || cmd == "--raw" )
  {
    if( argc < 4 )
    {
      printf("Error: Too few arguments\n");
      return 1;
    }

    std::string bufferType( argv[2] );
    std::string arg( argv[3] ); // file name or hex string

    std::vector<uint8_t> buffer;

    if( cmd == "--hex-auto" || cmd == "--hex" )
    {
      buffer = HexToBytes( arg );
    }
    else
    {
      std::ifstream infile(arg, std::ios_base::binary);
      buffer = std::vector<uint8_t> { std::istreambuf_iterator<char>(infile), std::istreambuf_iterator<char>() };
    }

    RawBuffer rawbuf( buffer.data(), buffer.size() );
    std::unique_ptr<ICatbuffer> cat;

    if( cmd == "--hex-auto" || cmd == "--raw-auto" )
    {
      cat = create_type( rawbuf, bufferType );
    }
    else if( cmd == "--hex" || cmd == "--raw" )
    {
      cat = create_type( bufferType );
      if( nullptr == cat )
      {
        printf( "\nError: Unknown buffer name '%s\n", bufferType.c_str() );
        return 1;
      }
      cat->Deserialize(rawbuf);
    }

    cat->Print();

    if( !cat )
    {
      printf( "Error: Was not able to deserialize data! Error occured at around byte: %lu\n", rawbuf.GetOffset() );
      return 1;
    }

  }

  printf("\nData deserialized successfully!\n\n");
  return 0;
}
