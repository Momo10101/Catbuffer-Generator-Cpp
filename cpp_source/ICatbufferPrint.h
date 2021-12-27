#pragma once

#include <cstdlib>
#include "RawBuffer.h"
#include "IPrettyPrinter.h"

class ICatbuffer : public IPrettyPrinter
{
public:

  virtual ~ICatbuffer(){}


  /**
   * Takes a raw byte buffer, deserializes it and populates the class fields.
   *
   * @param[in] buffer  The raw data which will be deserialized
   * @return            True if buffer contained enough data to deserialize all fields
   */
  virtual bool Deserialize( RawBuffer& buffer ) = 0;


  /**
   * Takes the transaction fields and deserializes them into a raw buffer
   *
   * @param[in] buffer  The raw buffer where fields will be serialized
   * @return            True if buffer contained enough data to deserialize all fields
   */
  virtual bool Serialize( RawBuffer& buffer ) = 0;


  /**
   * Returns the size of catbuffer in bytes, when serialized
   *
   * @return  Byte size of catbuffer
   */
  virtual size_t Size() = 0;

};
