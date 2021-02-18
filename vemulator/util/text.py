# Util functions related to sending and processing text messages

def check_checksum(message):
    """
    Check the checksum of a text message
    :param message: message to check
    :type message: bytes
    :return: true if valid, false otherwise
    :rtype: bool
    """

    # The sum of all the bytes in the message should be zero
    checksum = 0
    for byte in message:
        checksum = (checksum + byte) & 255
    return checksum == 0


def add_checksum(message):
    """
    Add a checksum to a text message
    :param message: message to add the checksum to
    :type message: bytes
    :return: the message with the checksum appended
    :rtype: bytes
    """

    # The sum of all the bytes in the message should be zero
    message += b'\r\nChecksum\t'
    checksum = 0
    for byte in message:
        checksum = (checksum + byte) & 255
    checksum = (256 - checksum) & 255
    message += checksum.to_bytes(1, 'big')
    return message


def bit_error(message, bit_error_rate, rand):
    """
    Add bit errors to a message
    :param message: message
    :type message: bytes
    :param bit_error_rate: bit error rate
    :type bit_error_rate: float
    :param rand: RNG
    :type rand: Random
    :return:
    """
    # Convert to a large integer value
    int_representation = int.from_bytes(message, 'big')
    # most significant byte is at the beginning of the byte array
    # This large integer value can now be converted to a binary representation (without 0b)
    bits = bin(int_representation)[2:]
    # Convert it to a list of bits
    bit_list = list(map(int, bits.zfill(8 * ((len(bits) + 7) // 8))))
    # Calculate the amount of bits that have to be corrupted
    amount_of_errors = round(bit_error_rate * len(bit_list))
    # Select the specific bit indices to corrupt
    to_corrupt = rand.sample(range(len(bit_list)), amount_of_errors)
    for x in to_corrupt: # Corrupt the bit indices
        bit_list[x] = int(not bool(bit_list[x]))

    # Create large integer again
    n = int(''.join(map(str, map(int, bit_list))), 2)
    # And convert to byte array
    return n.to_bytes((n.bit_length() + 7) // 8, 'big')