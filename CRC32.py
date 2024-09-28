from colorama import Fore, Style, init

def calculate_crc32(data: str) -> int:
    """
    Computes the CRC32 checksum for the given string using manual bitwise operations.
    
    Parameters:
    data (str): The input string for which the CRC32 checksum is calculated.

    Returns:
    int: The calculated CRC32 checksum as an integer.
    """
    # Convert the input string to a byte array using UTF-8 encoding.
    byte_data = data.encode('utf-8')
    
    # This is the standard polynomial used in CRC32 (bit-reversed version of 0x04C11DB7).
    polynomial = 0xEDB88320
    # Initialize the CRC value to all bits set to 1 (0xFFFFFFFF).
    crc = 0xFFFFFFFF

    # Iterate through each byte in the byte array.
    for byte in byte_data:
        # XOR the current byte with the least significant byte of the CRC value.
        crc ^= byte
        # Process each of the 8 bits in the byte.
        for _ in range(8):
            # If the least significant bit of the CRC is set (1),
            # XOR the current CRC value with the polynomial and shift right.
            if crc & 1:
                crc = (crc >> 1) ^ polynomial
            # If the least significant bit is not set (0),
            # just shift the CRC value to the right.
            else:
                crc >>= 1

    # After processing all bytes, invert the CRC value to get the final checksum.
    return crc ^ 0xFFFFFFFF

def run_crc_test():
    """
    Runs a test of the CRC32 calculation using a predefined string.
    Prints the CRC32 checksum in hexadecimal format with colors.
    """
    # Initialize colorama
    init(autoreset=True)

    # Define a test string to calculate the CRC32 checksum.
    test_string = "george"
    # Calculate the CRC32 checksum for the test string.
    crc_value = calculate_crc32(test_string)

    print(f"CRC32 of |{Fore.RED}{test_string}{Style.RESET_ALL}|: {Fore.GREEN}{crc_value:08X}{Style.RESET_ALL}")

# Main entry point for the script.
if __name__ == "__main__":

    run_crc_test()
