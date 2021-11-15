#include "RawBuffer.h"


RawBuffer::RawBuffer( uint8_t* ptr, const size_t size )
  : mPtr    ( ptr    ),
    mSize   ( size   ),
    mOffset ( 0      )
{

}


bool RawBuffer::CanRead( const size_t n ) const
{
  return ( (mSize - mOffset) >= n );
}


bool RawBuffer::MoveOffset( const size_t offset)
{
  if( mOffset + offset < mOffset ||   // overflow
      mOffset + offset > mSize      ) // exceed buffer size
  {
    return false;
  }

  mOffset += offset;

  return true;
}


uint8_t* RawBuffer::GetOffsetPtr( ) const
{
  return (mPtr + mOffset);
}


uint8_t* RawBuffer::GetOffsetPtrAndMove( const size_t n )
{
  uint8_t*   out  = GetOffsetPtr();
  const bool succ = MoveOffset(n);

  //printf("----> GetOffsetPtrAndMove: pointer: %p, n:%lu || size:%lu, offset:%lu, succ:%u\n", mPtr, n, mSize, mOffset, succ);

  if( !succ ) { out = nullptr; }

  return out;
}


size_t RawBuffer::TotalSize() const
{
  return mSize;
}


size_t RawBuffer::RemainingSize() const
{
  return mSize - mOffset;
}

size_t RawBuffer::GetOffset() const
{
  return mOffset;
}
