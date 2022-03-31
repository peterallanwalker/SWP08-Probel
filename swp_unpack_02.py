# SWP08 unpack 
# Identifies, validates and Extracts SWP08 messages from byte strings
# Peter Walker, June 2021.

# ver 2 in progress,
# deal with DLE DLE
# get checksum verification working
# have a test debug mode to chek all messages in ones we dont support cant unpack
# handle ACK/NAK.


import swp_utils as utils


def _find_header(data: bytes) -> int:
    """ Checks for SWP08 protocol's SOM (start of message header) 
            within passed byte string
        Returns index of potential first byte of SOM if found, -1 if not found.
        :param data: bytes
        :return: int
    """
    for i, byte in enumerate(data):
        if byte == utils.SOM[0]:
            return i
    return -1


def _is_checksum_valid(message, header_byte, byte_count):
    # TODO - NOT CURRENTLY USING THIS - SHOULD DO - NEED TO ADAPT FOR SWP08
    message_checksum = message[header_byte + utils.CSCP_HEADER_LENGTH + byte_count]
    compare_checksum = 0

    # Loop through payload bytes
    for i in range (header_byte + utils.CSCP_HEADER_LENGTH, header_byte + utils.CSCP_HEADER_LENGTH + byte_count):
        compare_checksum += message[i]

    compare_checksum = utils.twoscomp(bin(compare_checksum))

    if message_checksum == int(compare_checksum, 16):
        return True
    else:
        return False


def unpack_data(data, previous_insufficient_data=False):
    """ Takes bytes, (and any residual bytes returned from previous call).
        Extracts and returns valid CSCP messages found within
        also returns any residual data from the end that could be the beginning of a valid message
        (with remainder of message in next bytes to be received - to supply to this function in next call)

    :param data: bytes
    :param previous_insufficient_data: bytes (possible start of message from preceding data)
    :return: bytes, bytes or bool (extracted messages, residual data that may be beginning of message who's remainder
                is due in next received data
    """
    
    if previous_insufficient_data:
        data = previous_insufficient_data + data

    messages = []
    insufficient_data = False

    # - FOR DEBUG, print raw received - #
    print("\n[swp_unpack.unpack_data]: DATA DUMP - ", data)

    while len(data) > 0:
        header_byte = _find_header(data)  # First index within data containing a CSCP start of header value (0xF1 / 241)
        if header_byte != -1:
            #print("[SWP08_unpack]: processing data:", data)
            #print("[SWP08_unpack]: potential header found at index", header_byte)
            #print("SWP_unpack", data)
            if header_byte + 10 >= len(data):  # Connect & COnnected messages are 11 bytes long TODO - handle other message types.
                #print("[SWP08_unpack]: insuficcient data for complet message")
                insufficient_data = data[header_byte:]
                break
            
            if data[header_byte + 9] == utils.EOM[0] and data[header_byte + 10] == utils.EOM[1]:
                #print("[SWP08_unpack]: SOM & EOM FOUND. Extracted message:", data[header_byte : header_byte + 11])
                # TODO! - PROPERLY VALIDATE MESSAGES USING CHECKSUM & BYTE COUNT, + HANDLE OTHER MESSAGE TYPES
                messages.append(data[header_byte : header_byte + 11])
                data = data[header_byte + 11:]

            else:
                #print ('invalid header - EOM not found,  discarding!')
                data = data[header_byte+1:]  # Discard processed header.

        else:
            break  # No more SWP start of message headers found

    #print ('messages extracted:', messages, ' insufficient_data:', insufficient_data)
    return messages, insufficient_data


if __name__ == '__main__':

    test_data = b'\x10\x02\x04\x00\x00\x0c\x02\x05\xe9\x10\x03\x10\x02\x04\x00\x00\r\x03\x05\xe7\x10\x03'
    
    messages, residual_data = unpack_data(test_data)
    for msg in messages:
        print(msg)
        
    print(residual_data)

