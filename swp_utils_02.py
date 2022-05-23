# - Constants and utility functions for working with the SWP08/Probel protocol
# - Peter Walker, May 2022.
#
# - Protocol doc:
# -   https://github.com/peterallanwalker/SWP08-Probel/blob/master/protocol%20docs/SW-P-08%20Issue%2032.pdf
#
# - Message Structure (protocol doc page 9):
# -   SOM, DATA, BYTE-COUNT, CHECKSUM, EOM
# -   DATA = Command Byte + payload
# -     Max size of DATA should be 128 bytes (before DLE padding/escaping)
# -   BYTE-COUNT = Number of bytes in DATA

import cli_utils

TITLE = "SWP08 utilities"
VERSION = 1.1

# - SPECIAL VALUES
# - DLE is a special value used to identify SOM/EOM. Wherever 0x10/16 is within payload it should be escaped
# - (by duplicating it, i.e. b'\x10\x10' represents a single 0x10 value outside of a SOM/EOM
DLE = 16
SOM = [DLE, 2]  # - SWP message header ("Start of Message")
EOM = [DLE, 3]  # - SWP message end ("End of Message")
ACK = bytes([DLE, 6])  # - Acknowledged message returned by router on receipt of a valid message.
NAK = bytes([DLE, 21])  # - Not Acknowledged message returned by router on receipt of an invalid message.

COMMAND_BYTE = 2  # - Command type is the 3rd byte of any SWP message other than ACK/NAK (first byte after SOM)
MATRIX_LEVEL_BYTE = 3  # - For Connect, Connected, Push Labels, Push Labels Extended (+ others)
SOURCE_BYTE = 6  # - For Connect & Connected messages
DESTINATION_BYTE = 5  # - For Connect, Connected, Push Labels, Push Labels Extended (+ others)
MULTIPLIER_BYTE = 4  # - For Connect/Connected messages
CHAR_LEN_BYTE = 4  # - For Push Labels / Push Labels Extended messages
LABEL_QTY_BYTE = 7  # - For Push Labels / Push Labels Extended messages
FIRST_LABEL_CHAR_BYTE = 8  # - For Push Labels / Push Labels Extended messages

COMMANDS = {"connect": 2,  # Send to router to make a connection.
            "connected": 4,  # Received from router when a connection is made.
            "push_labels": 107,
            "push_labels_extended": 235,
            "cross-point tally dump request": 21,
            "cross-point tally dump (byte)": 22,
            "cross-point tally dump (word/extended)": 23,
            }

# LABEL MESSAGE LENGTH CODES, keys - num chars, values - coded value
CHAR_LEN_CODES = {4: 0, 8: 1, 12: 2, 16: 3, 32: 4}


def is_same_matrix_and_level(source, destination):
    """
    :param source: Node object
    :param destination: Node object
    :return: Boolean
    """
    if source.matrix == destination.matrix and source.level == destination.level:
        return True
    else:
        return False


def encode_matrix_level(matrix, level):
    """
    Protocol doc section 3.1.2, page 13.
    Encodes matrix & level into a single byte, bits 0-3 for level, bits 4-7 for matrix
    :param matrix: int
    :param level: int
    :return: int representing matrix and level
    """
    if matrix not in range(16) or level not in range(16):
        error_message = "[swp_utils.encode_matrix_level]: Matrix and level need to be within range 0 to 15, " \
                        "values passed - matrix: {}, level: {}" \
            .format(matrix, level)
        raise ValueError(error_message)

    # - Convert values to 4 bit binary
    matrix = format(matrix, '04b')
    level = format(level, '04b')
    # - Concatenate to 8 bits and return as decimal int
    return int(matrix + level, 2)


def encode_multiplier(source, destination):
    """
    Protocol doc section 3.1.2, page 13
    The multiplier byte allows source and destination IDs up to 1023 to be used
    :param source: int in range 0-1023
    :param destination: int in range 0-1023
    :return: int, decimal, encoded multiplier for the given source and destination IDs
    """
    if source not in range(1024) or destination not in range(1024):
        error_message = "[swp_utils.encode_multiplier]: Source and destination IDs must be in range 0 to 1023, " \
                        "\n\tReceived Source: {}, Destination: {}".format(source, destination)
        raise ValueError(error_message)

    bit7 = '0'
    bit3 = '0'
    # - Multiplier values are source/dest DIV 128
    # - Using format to convert dec values to binary padded to 3 bits
    bits4_6 = format(int(destination / 128), '03b')
    bits0_3 = format(int(source / 128), '03b')
    binary_num = '0b' + bit7 + bits4_6 + bit3 + bits0_3
    return int(binary_num, 2)


def decode_matrix_level(msg):
    d = msg[MATRIX_LEVEL_BYTE]
    d = format(d, '08b')  # converted to 8bit binary
    matrix = d[:4]  # - 4 MSBs (bits 4-7)
    level = d[4:]  # - 4 LSBs (bits 0-3)
    matrix = int(matrix, 2)
    level = int(level, 2)
    return matrix, level


def calculate_checksum(data):
    """
        Calculates and returns a checksum for an SWP08 message.
        :param data: list of byte values that make up the message payload
            [command byte, data byte 1, ... , data byte n, byte-count byte]
        :return: int - decimal value of checksum for data
    """
    checksum = 0
    for value in data:
        checksum += value

    return twos_compliment(checksum)


def twos_compliment(value):
    """
    :param value: int (decimal)
    :return: int - decimal two's compliment of the received value
    """
    # - https://stackoverflow.com/questions/16926130/convert-to-binary-and-keep-leading-zeros
    # - https://docs.python.org/2/library/string.html#format-specification-mini-language
    # - Convert to 8 bit binary value
    value = format(value, '08b')
    # - Invert the bits
    value = ''.join('1' if x == '0' else '0' for x in value)
    # - Add one, as per two's compliment
    value = int(value, 2) + 1

    # - If result is larger than 1 byte...
    if value > 255:
        value = bin(value)[-8:]  # - Convert to binary and take the last 8 bits
        value = int(value, 2)  # - Convert back to decimal int

    return value


def set_label_length(labels, length):
    """
    Check label lengths and truncate if necessary
    :param labels: list of strings
    :param length: int - number of chars for label format.
    :return: list of strings
    """
    valid_label_lengths = (4, 8, 12, 16, 32)
    if length not in valid_label_lengths:
        raise ValueError("[swp_utils.truncate_labels]: Invalid character length: {}, must be one of: {}".
                         format(length, valid_label_lengths))
    else:
        fixed_len = []
        for label in labels:
            if len(label) > length:
                # - Truncate long labels
                fixed_len.append(label[:length])
            else:
                # - Pad short labels (also passes labels that are already the correct length)
                fixed_len.append(label.ljust(length))
        return fixed_len


def format_labels(labels):
    """
    :param labels: List of strings
    :return: list of strings converted to their decimal ASCII values
    """
    r = []
    for label in labels:
        for char in label:
            r.append(ord(char))
    return r


def decode_connect_source_destination(encoded_message):
    """
    Parses Connect (02) and Connected (04) messages to extract source and destination IDs
    :param encoded_message: bytes - valid encoded SWP message
    :return: int, int - source ID, destination ID
    """
    source = encoded_message[SOURCE_BYTE]
    destination = encoded_message[DESTINATION_BYTE]
    # - Converted byte to 8 bit binary string using format
    multiplier = format(encoded_message[MULTIPLIER_BYTE], '08b')
    source_multiplier = multiplier[-3:]  # - bits 0-2 (3 LSBs)
    dest_multiplier = multiplier[-7:-4]  # - bits 4-6
    source += int(source_multiplier, 2) * 128
    destination += int(dest_multiplier, 2) * 128
    return source, destination


def decode_labels_destination(msg):
    """
    Return the destination ID of a push_labels (107) / push_labels_extended (235) message
    :param msg: byte string - validated encoded label message
    :return: int - ID of the (first) destination
    """
    div = msg[DESTINATION_BYTE]
    mod = msg[DESTINATION_BYTE + 1]
    return 256 * div + mod


def get_labels(msg):
    """
    :param msg: byte string - validated encoded push labels or push labels extended message
    :return: list of strings - labels
    """
    label_qty = msg[LABEL_QTY_BYTE]
    char_len = list(CHAR_LEN_CODES.keys())[list(CHAR_LEN_CODES.values()).index(msg[CHAR_LEN_BYTE])]
    labels = []
    i = FIRST_LABEL_CHAR_BYTE
    for _ in range(label_qty):
        label = ''
        for letter in range(char_len):
            label += chr(msg[i])
            i += 1
        labels.append(label)

    #print("DEBUG CHAR LEN:", char_len)
    #print("DEBUG LABEL QTY:", label_qty)
    return labels


def test_get_labels():
    test_messages = [b'\x10\x02k\x00\x02\x00\x00\none         two         three       four        five        six'
                     b'         seven       eight       nine        ten         ~Z\x10\x03',
                     b'\x10\x02k\x00\x01\x00\x00\x06testing eight   char    labels  so      some ver65\x10\x03']

    test_label_lens = [12, 8]  # - label lengths passed in test_messages
    for msg in test_messages:
        print(get_labels(msg))


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)
    print("Tests...")
    test_get_labels()

