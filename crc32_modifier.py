import os, sys, zlib
from typing import BinaryIO, List, Optional, Tuple

# ---- Main application ----

def main(args: List[str]) -> Optional[str]:
    """
    Main entry point for the script. Handles command-line arguments, validates them,
    and processes the file to modify its CRC32 checksum.
    
    Parameters:
    args (List[str]): List of command-line arguments.

    Returns:
    Optional[str]: Error message if any, otherwise None.
    """
    # Check if the correct number of arguments is passed
    if len(args) != 3:
        return "Usage: python crc32_modifier.py <FileName> <ByteOffset> <NewCrc32Value>"

    # Validate and convert the byte offset argument
    try:
        offset: int = int(args[1])
    except ValueError:
        return "Error: Invalid byte offset"
    if offset < 0:
        return "Error: Negative byte offset"

    # Validate the new CRC-32 value argument
    try:
        if len(args[2]) != 8 or args[2].startswith(("+", "-")):
            return "Error: Invalid new CRC-32 value"
        temp: int = int(args[2], 16)  # Convert hex string to integer
        if temp & MASK != temp:
            return "Error: Invalid new CRC-32 value"
        new_crc: int = reverse32(temp)  # Reverse the CRC-32 value
    except ValueError:
        return "Error: Invalid new CRC-32 value"

    # Attempt to process the file
    try:
        modify_file_crc32(args[0], offset, new_crc, True)
    except IOError as e:
        return "I/O error: " + str(e)
    except ValueError as e:
        return "Error: " + str(e)
    except AssertionError as e:
        return "Assertion error: " + str(e)

    return None

def modify_file_crc32(path: str, offset: int, newcrc: int, printstatus: bool = False) -> None:
    """
    Modifies the CRC-32 value at a specific byte offset in a file.

    Parameters:
    path (str): Path to the file.
    offset (int): Byte offset to apply the patch.
    newcrc (int): New CRC-32 value to apply.
    printstatus (bool): If True, prints status messages. Default is False.
    """
    # Open the file in read/write binary mode
    with open(path, "r+b") as raf:
        # Move to the end of the file to get its length
        raf.seek(0, os.SEEK_END)
        length: int = raf.tell()
        if offset + 4 > length:
            raise ValueError("Byte offset plus 4 exceeds file length")
        
        # Calculate the original CRC-32 value of the entire file
        crc: int = get_crc32(raf)
        if printstatus:
            print(f"Original CRC-32: {reverse32(crc):08X}")

        # Calculate the difference needed to update the CRC-32 value
        delta: int = crc ^ newcrc
        delta = multiply_mod(reciprocal_mod(pow_mod(2, (length - offset) * 8)), delta)

        # Modify the 4 bytes at the specified offset
        raf.seek(offset)
        bytes4: bytearray = bytearray(raf.read(4))
        if len(bytes4) != 4:
            raise IOError("Cannot read 4 bytes at offset")
        for i in range(4):
            bytes4[i] ^= (reverse32(delta) >> (i * 8)) & 0xFF

        # Write the modified bytes back into the file
        raf.seek(offset)
        raf.write(bytes4)
        if printstatus:
            print("Computed and wrote patch")

        # Verify the CRC-32 value to ensure correctness
        if get_crc32(raf) != newcrc:
            raise AssertionError("Failed to update CRC-32 to desired value")
        elif printstatus:
            print("New CRC-32 successfully verified")

# Polynomial and mask used in CRC-32 calculations
POLYNOMIAL: int = 0x104C11DB7  # CRC-32 polynomial (do not modify, dependencies rely on this)
MASK: int = (1 << 32) - 1  # Mask to keep values within 32 bits

def get_crc32(raf: BinaryIO) -> int:
    """
    Computes the CRC-32 checksum of the file.

    Parameters:
    raf (BinaryIO): Open file object in binary mode.

    Returns:
    int: The CRC-32 checksum as an integer.
    """
    raf.seek(0)  # Go to the beginning of the file
    crc: int = 0
    while True:
        # Read file data in chunks (128 KB) and compute the CRC-32 incrementally
        buffer: bytes = raf.read(128 * 1024)
        if len(buffer) == 0:
            return reverse32(crc)  # Return reversed CRC-32 result
        crc = zlib.crc32(buffer, crc)

def reverse32(x: int) -> int:
    """
    Reverses the bits in a 32-bit integer.

    Parameters:
    x (int): The 32-bit integer to reverse.

    Returns:
    int: The reversed 32-bit integer.
    """
    y: int = 0
    for _ in range(32):
        y = (y << 1) | (x & 1)  # Shift left and add the least significant bit
        x >>= 1  # Shift the input to the right
    return y

def multiply_mod(x: int, y: int) -> int:
    """
    Multiplies two integers modulo POLYNOMIAL using Russian peasant multiplication.

    Parameters:
    x (int): First integer.
    y (int): Second integer.

    Returns:
    int: The result of (x * y) % POLYNOMIAL.
    """
    z: int = 0
    while y != 0:
        if y & 1:
            z ^= x  # Add x to z if y's LSB is 1
        y >>= 1  # Shift y to the right
        x <<= 1  # Double x
        if (x >> 32) & 1 != 0:  # Apply modulo reduction by POLYNOMIAL
            x ^= POLYNOMIAL
    return z

def pow_mod(x: int, y: int) -> int:
    """
    Raises a number to a power modulo POLYNOMIAL using exponentiation by squaring.

    Parameters:
    x (int): Base number.
    y (int): Exponent.

    Returns:
    int: The result of (x^y) % POLYNOMIAL.
    """
    z: int = 1
    while y != 0:
        if y & 1 != 0:
            z = multiply_mod(z, x)
        x = multiply_mod(x, x)
        y >>= 1
    return z

def divide_and_remainder(x: int, y: int) -> Tuple[int, int]:
    """
    Performs division and returns both the quotient and remainder.

    Parameters:
    x (int): Dividend.
    y (int): Divisor.

    Returns:
    Tuple[int, int]: Quotient and remainder.
    """
    if y == 0:
        raise ValueError("Division by zero")
    if x == 0:
        return (0, 0)

    ydeg: int = get_degree(y)
    z: int = 0
    for i in range(get_degree(x) - ydeg, -1, -1):
        if (x >> (i + ydeg)) & 1 != 0:
            x ^= y << i  # Subtract shifted divisor from x
            z |= 1 << i  # Set the bit in the quotient
    return (z, x)

def reciprocal_mod(x: int) -> int:
    """
    Finds the multiplicative inverse of x modulo POLYNOMIAL using the extended Euclidean algorithm.

    Parameters:
    x (int): Input integer.

    Returns:
    int: Multiplicative inverse of x modulo POLYNOMIAL.
    """
    y: int = x
    x = POLYNOMIAL
    a: int = 0
    b: int = 1
    while y != 0:
        q, r = divide_and_remainder(x, y)  # Get quotient and remainder
        c = a ^ multiply_mod(q, b)
        x = y
        y = r
        a = b
        b = c
    if x == 1:
        return a  # Return the inverse if it exists
    else:
        raise ValueError("Reciprocal does not exist")

def get_degree(x: int) -> int:
    """
    Returns the degree (position of the highest set bit) of a given integer.

    Parameters:
    x (int): Input integer.

    Returns:
    int: Degree of the integer.
    """
    return x.bit_length() - 1

# Program entry point
if __name__ == "__main__":
    errmsg = main(sys.argv[1:])  # Call main function with command-line arguments
    if errmsg is not None:
        sys.exit(errmsg)  # Exit with an error message if there was an issue
