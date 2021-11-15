#pragma once
#include <cstdint>
#include <stddef.h>



/**
 * A class to handle a raw byte buffer/array. It is used for moving an offset
 * within a buffer in order to read and convert data. It offers simple bounds
 * checking when moving offset.
 *
 *                         mSize
 *                ___________|____________
 *               |                        |
 *  byte buffer:  [0|1|2|3|4|5|6|7| .... ]
 *                ↑            ↑
 *              mPtr        mOffset
 */
class RawBuffer
{
 public:
  RawBuffer( uint8_t* ptr, const size_t size );

  /**
   * Returns true if 'n' bytes, relative to offset, can be read from buffer,
   * without going out of bounds.
   *
   * @param[in] n
   *   Number of bytes to read from buffer.
   *
   * @return true if success, false otherwise.
   */
  bool CanRead( const size_t n ) const;


  /**
   * Moves offset 'n' bytes relative to current offset.
   *
   * @param[in] n
   *   Move offset 'n' bytes relatively to current offset.
   *
   * @return
   *   False if buffer does not contain sufficient bytes relative to
   *   current offset
   *
   */
  bool MoveOffset( const size_t offset);


  /**
   * Returns pointer to current offset within buffer.
   *
   * @param[in] buffer
   *   Pointer to current offset.
   *
   * @return pointer to current offset within buffer
   */
  uint8_t* GetOffsetPtr( ) const;


  /**
   * Returns pointer to current offset within buffer, and then moves offset 'n'
   * bytes relative to current offset.
   *
   * @param[in] n
   *   Number of bytes to move offset relatively to current offset
   *
   * @return
   *   Pointer to current offset within buffer, or null pointer if buffer
   *   does not contain sufficient bytes relative to current offset
   */
  uint8_t* GetOffsetPtrAndMove( size_t n );


  /**
   * The total size of the buffer.
   */
  size_t TotalSize() const;


  /**
   * The remaining size of buffer, relative to offset.
   */
  size_t RemainingSize() const;


  /**
   * Returns the offset position compared to the start of the buffer
   */
  size_t GetOffset() const;


 private:
        uint8_t* mPtr;    ///< Pointer to start of byte buffer
  const size_t   mSize;   ///< Size of all of byte buffer
        size_t   mOffset; ///< Offset in buffer relative to 'mPtr'
};
