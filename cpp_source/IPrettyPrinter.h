#pragma once

#include <cstdlib>
#include "RawBuffer.h"

class IPrettyPrinter
{

 public:

  virtual ~IPrettyPrinter(){}

	/**
	 * Prints a deserialized catbuffer.
	 *
	 * @param[in] level  Controls the indentation when printing a buffer
	 */
  virtual void Print( const size_t level=0 ) = 0;
};
