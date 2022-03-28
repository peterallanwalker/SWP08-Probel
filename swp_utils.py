# SWP08 UTILITIES
# Constants and helper functions for working with the SWP08 router control protocol
# Peter Walker, June 2021
#
# Updated March 2022 - added support for pushing labels.
# ... Note this is not typical usage of the protocol,
#     it is used by VSM to push labels to Calrec Apollo/Artemis audio mixers

# SWP08 protocol info:
# https://wwwapps.grassvalley.com/docs/Manuals/sam/Protocols%20and%20MIBs/Router%20Control%20Protocols%20SW-P-88%20Issue%204b.pdf
# Other versions of the protocol doc are available in the project's protocol docs folder

# - CONSTANTS
SOM = [0x10, 0x02]  # SWP08 Message header ("Start Of Message")
EOM = [0x10, 0x03]  # SWP08 Message end ("End of Message")

COMMAND_BYTE = 2    # Command type is set in the 3rd byte of an SWP08 message
SOURCE_BYTE = 6
DESTINATION_BYTE = 5

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


def twos_compliment(value):
    """
    :param value: integer
    :return: integer - two's compliment of the received value
    """
    # TODO - I've made a meal out of this, it works, but there must be a more elegant and concise way!

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
