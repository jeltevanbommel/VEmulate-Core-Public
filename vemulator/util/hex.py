# Util functions related to sending and processing hex messages
import codecs


def calculate_checksum(message):
    """
    Calculate the checksum of a hex message
    :param message: message as hex string that contains the command and the data (so not the colon, newline or checksum)
    :type message: str
    :return: checksum as string
    :rtype: str
    """

    # Make sure it is a valid hex string
    if len(message) % 2 == 1:
        message = '0' + message

    # Get bytes
    message_bytes = bytes.fromhex(message)

    # The sum of all the bytes should be 0x55
    check = 0
    for byte in message_bytes:
        check = (check + byte) & 0xFF
    checksum = (0x55 - check) & 0xFF
    return '{:02x}'.format(checksum).upper()


def check_checksum(message):
    """
    Check the checksum of a hex message
    :param message: message as hex string
    :type message: text
    :return: true if valid, false otherwise
    :rtype: bool
    """

    checksum = calculate_checksum(message[:-2])

    return checksum == message[-2:]


def create_message(command, payload=''):
    """
    Create a new hex message
    :param command: command ID
    :type command: int or str
    :param payload: payload of the message
    :type payload: str
    :return: hex message as binary string, including the calculated checksum
    :rtype: bytes
    """
    message = str(command) + payload
    return bytes(':' + message + calculate_checksum(message) + '\n', 'ascii')


def int_to_hex_string(value, byte_size, signed=False, little_endian=True):
    """
    Convert an integer to a little endian hex string
    :param value: integer value to convert
    :type value: int
    :param byte_size: byte size of the hex encoded integer
    :type byte_size: int
    :param signed: should be true if the integer is a signed integer
    :type signed: bool
    :return: hex representation of the integer
    :rtype: str
    """
    return codecs.encode(value.to_bytes(byte_size, 'little' if little_endian else 'big', signed=signed), 'hex').decode('utf-8').upper()


def string_to_hex_string(value, byte_size=None):
    """
    Convert a text string to a hex representation of the string
    :param value: string to convert
    :type value: any
    :param byte_size: byte size of the string, will take the byte length of the input string by default
    :type byte_size: int
    :return: hex representation of the string
    :rtype: str
    """
    hex_value = codecs.encode(str(value).encode(), 'hex').decode('utf-8').upper()
    if byte_size is not None:
        return hex_value.ljust(byte_size * 2, '0')
    else:
        return hex_value


def value_to_hex_string(value, byte_size=None, signed=False):
    """
    Convert an integer or a text string to a hex string
    If the value is of type int, int_to_hex string is used, otherwise, string_to_hex_string is used
    :param value: value
    :type value: int or str
    :param byte_size: byte size of the string, will take the byte length of the input string by default if value is a string
    :type byte_size: int
    :param signed: should be true if the integer is a signed integer
    :type signed: bool
    :return: hex representation of the string
    :rtype: str
    """
    if isinstance(value, int):
        return int_to_hex_string(value, byte_size, signed)
    else:
        return string_to_hex_string(value, byte_size)
