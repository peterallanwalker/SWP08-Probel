# SWP08 UTILITIES
# Constants and helper functions for working with the SWP08 router control protocol
# Peter Walker, June 2021
#
# Updated March 2022 - added support for pushing labels.
# ... Note this is not typical usage of the protocol,
#     it is used by VSM to push labels to Calrec Apollo/Artemis audio mixers
#
# SWP08 protocol info:
# https://wwwapps.grassvalley.com/docs/Manuals/sam/Protocols%20and%20MIBs/Router%20Control%20Protocols%20SW-P-88%20Issue%204b.pdf
# Other versions of the protocol doc are available in the project's protocol docs folder

import cli_utils

# This file
import swp_utils

TITLE = "SWP08 utilities"
VERSION = 1.0

# - CONSTANTS
DLE = 0x10  # - DLE is a special value used to identify headers/EOM. Wherever DLE/0x10/16 is used within payload, it should be duplicated DLE DLE to differentiate
SOM = [0x10, 0x02]  # SWP08 Message header ("Start Of Message")
EOM = [0x10, 0x03]  # SWP08 Message end ("End of Message")
ACK = [0x10, 0x06]  # Returned by router to acknowledge receipt of a valid message
NAK = [0x10, 0x15]  # Returned by router if message is not valid (e.g. wrong format/byte-count/checksum)

COMMAND_BYTE = 2    # Command type is set in the 3rd byte of an SWP08 message

# - FOLLOWING ARE ONLY CORRECT FOR CONNECT AND CONNECTED MESSAGES...
# - TODO - provide a more genric way of looking up source/dest bytes based on message type
# - ... actually byte 5 is the destination DIV for a label message
SOURCE_BYTE = 6
DESTINATION_BYTE = 5
MULTIPLIER_BYTE = 4  # Connect/Connected messages

COMMANDS = {"connect": 0x02,    # Send to router to set a connection
            "connected": 0x04,  # Sent from router when a connection is made
            "push_labels": 107,
            "push_labels_extended": 235,
            }

CHAR_LEN_CODES = {4: 0,
                  8: 1,
                  12: 2,
                  16: 3,
                  32: 4
                  }


# - HELPER FUNCTIONS

def calculate_checksum(data):
    """
        Calculates and returns a checksum for an SWP08 message.
        :param data: takes an array/list of values,
            one per byte of an SWP08 message's DATA and BTC (byte count),
            e.g. [<COMMAND byte>, <DATA byte 1>, ... , <DATA byte n>, <BTC - byte count>]

    """
    checksum = 0
    for value in data:
        checksum += value

    return twos_compliment(checksum)


def is_checksum_valid(message):
    message = message[2: -2]  # - Strip SOM & EOM
    message_checksum = message[-1]  # - Last byte
    message = message[:-1]  # - Strip checksum
    # need to pass list of bytes to calculate_checksum, not byte string
    payload = [b for b in message]  # - Bytes from bytestring to list of bytes
    compare_checksum = calculate_checksum(payload)

    if message_checksum == compare_checksum:
        return True
    else:
        return False


def twos_compliment(value):
    """
    :param value: integer
    :return: integer - two's compliment of the received value
    """
    # TODO - I've made a meal out of this, it works, but there must be a more elegant and concise way!
    # TODO - replace manual padding to 8 bits with format(<value>, '#010b')
    #  - takes decimal value converts to binary string padded with zeroes to 10 chars (includes '0b' at the begining
    # https://stackoverflow.com/questions/16926130/convert-to-binary-and-keep-leading-zeros
    # https://docs.python.org/2/library/string.html#format-specification-mini-language

    value = bin(value)  # Convert to a binary string.
    missing = 10 - len(value)  # Check supplied value is 8 bits (accounting for it being a string, prefixed with "0b"

    result = missing * "1"  # Pad out missing 8 bit MSB 0's with 1's (inverting as part of 2's comp)

    for bit in range(2, len(value)):  # get rid of the "0b" at the beginning of the binary string and loop through bits
        # invert bits
        if value[bit] == "1":
            result += "0"
        elif value[bit] == "0":
            result += "1"

    # add one to the result
    result = int(result, 2) + 1  # TODO, should be able to +1 without converting to int

    # If result is larger than 1 byte, trim to 1 byte by taking just the 8 least significant bits
    if result > 255:
        result = bin(result)     # Convert back to binary
        result = (result[-8:])   # Take last 8 bits
        result = int(result, 2)  # Convert back to decimal int

    return result


def get_labels_destination(msg):
    """
    Return the destination ID of a push_labels (107) / push_labels_extended (235) message
    :param msg: byte string - validated encoded label message
    :return: int - ID of the (first) destination
    """
    div = msg[DESTINATION_BYTE]
    mod = msg[DESTINATION_BYTE + 1]
    return 256 * div + mod


def encode_multiplier(source, destination):
    """
    Creates the multiplier byte as used in Connect and Connected messages
    ... This byte needs to be correctly set in order to pass source/destination ID values > 255, up to a max of 1023
    (think you're suppose to be able to pass IDs up into the 10's of thousands though, not sure how yet!)
    :param source: int - source id
    :param destination: int - destination id
    :return: encoded multiplier byte
    """

    if source > 1024 or destination > 1024:
        # TODO prevent input or handle > 1024 (should be able to handle much bigger numbers)
        print("[swp_utils.encode_multiplier]: WARNING! Source & Destination IDs must be within range 0 - 1024" 
              " (received Source:{}, Destination:{})".format(source, destination))
        return False

    bit7 = '0'
    bit3 = '0'

    # - using format to convert dec to binary and pad to 3 bits
    # - (5 - includes '0b' prefix)
    bits4_6 = format(int(destination / 128), '03b')
    bits0_3 = format(int(source / 128), '03b')
    binary_num = '0b' + bit7 + bits4_6 + bit3 + bits0_3
    return int(binary_num, 2)


def decode_source_destination(msg):
    """
    Parses Connect (02) & Connected (04) messages to extract source and destination IDs
            using the multiplier byte (that allows for IDs > 255, but limited to 1024)
    :param msg: bytestring - validated swp message
    :return: int, int, source ID, destination ID
    """
    # TODO - shouldnt need to have this check here
    #  as I'll only be calling this on message types that have a multiplier byte
    if msg[COMMAND_BYTE] not in (COMMANDS["connect"], COMMANDS["connected"]):
        print("[swp_utils.decode_source_destination]: This function only supports Connect(02)/Connected(04) messages,"
              " {} passed".format(msg[COMMAND_BYTE]))
        return False, False

    source = msg[SOURCE_BYTE]
    destination = msg[DESTINATION_BYTE]
    multiplier = format(msg[MULTIPLIER_BYTE], '08b')  # - byte converted to 8 bit binary string using format
    source_mult = multiplier[-3:]  # - 3 LSBs (bits 0-2)
    dest_mult = multiplier[-7:-4]   # - bits 4-6

    source += int(source_mult, 2) * 128
    destination += int(dest_mult, 2) * 128

    return source, destination


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)

