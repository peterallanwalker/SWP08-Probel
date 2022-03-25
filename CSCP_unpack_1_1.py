# CSCP_unpack - Validates and Extracts CSCP messaged from serial data bytes

# TODO - document and refactor
# TODO - check invalid checksums from the unsolicited data set - am I missing valid messages?

import time
import CSCP_utils_1_0 as utils  # my local file  # TODO - move checksum calculator to here so can be used in CSCP_pack as well


def _find_header(data: bytes) -> int:
    """ Checks for CSCP protocol's SOH (start of header value - 0xF1 / dec 241w) within received data.
        Returns index of first SOH if found, -1 if not found.
    :param data: bytes
    :return: int
    """
    for i, byte in enumerate(data):
        if byte == utils.CSCP_HEADER_START:
            return i
    return -1


def _is_checksum_valid(message, header_byte, byte_count):
    # TODO - make generic checksum creator for building messages and validating (replace the compare below)
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

    if len(data) == 1 and data[0] == 0x04:  # ACK recieved as single byte - TODO - check if ACKs are always on their own in a 1024 receive?
        print('received ACK')
        return data, False

    elif len(data) == 1 and data[0] == 0x05:  # NAK
        print('NOT ACKNOWLEDGED!')
        return data, False

    if previous_insufficient_data:
        data = previous_insufficient_data + data # TODO - test this

    messages = []
    insufficient_data = False

    while len(data) > 0:
        header_byte = _find_header(data)  # First index within data containing a CSCP start of header value (0xF1 / 241)
        if header_byte != -1:

            if header_byte + 1 == len(data):  # SOH found in last byte
                insufficient_data = data[header_byte:]
                break

            byte_count = data[header_byte + utils.BYTE_COUNT_BYTE]
            checksum_byte = header_byte + utils.CSCP_HEADER_LENGTH + byte_count
            total_message_length = byte_count + 4  # CSCP byte count value excludes, SOH, BC, DEV, and Checksum bytes

            if total_message_length > len(data):
                #print ('CSCP SOH found but no checksum - either invalid SOH or remainder of message to follow in next received data')
                insufficient_data = data[header_byte:]     # if no further header bytes found, this could be the start of a valid message continued in next data to be received
                data = data[header_byte + 1:]  # discard this header byte for next loop

            elif _is_checksum_valid(data, header_byte, byte_count):
                insufficient_data = False
                #print('\nvalid CSCP message found')
                preceding_data = data[:header_byte]  # TODO - don't discard, try adding to end of previoulsy received data to see if valid message spans two data blocks
                #print('preceding data - {}'.format(preceding_data))

                message = data[header_byte:checksum_byte+1]
                #print('message - {}'.format(message))
                messages.append(message)
                byte_count = data[header_byte + utils.BYTE_COUNT_BYTE]
                data = data[checksum_byte+1:]  # Discard processed message for next loop
                #print('remaining data - {}'.format(data))


            else:
                print ('invalid checksum')
                data = data[checksum_byte+1:]  # Discard processed message for next loop

        else:
            break  # No more CSCP start of headers found

    #print ('messages extracted:', messages, ' insufficient_data:', insufficient_data)
    return messages, insufficient_data


if __name__ == '__main__':

    test_data = [b'\xf1\x06\x00\x80\x00\x00\x03\x02\xE8\x93',  # Example of data containing single known good message
                    b'\x80\xf1\x06\x00\x80\x00\x00\x03\x02\xE8\x93\x90',  # Same data with random stuff prefixed and suffixed
                    b'\xf1\x86\x00\xf1\x06\x00\x80\x00\x00\x03\x02\xE8\x93\x90',  # half message at beginning
                    b'\x80\xf1\x06\x00\x80\x00\x00\x03\x02\xE8\x93\x90\x80\xf1\x06\x00\x80\x00\x00\x03\x02\xE8\x93\x90 ',
                    b'\x80\xf1\x06\x00\x80\x00\x00\x03\x02\xE8\x93\x90\x80\xf1\x06\x00\x80\x00\x00\x03\x02\xE8\x93\x90\xf1\x06\x00\x80',
                    b'\x80\xf1\x06\x00\x80\x00\x00\x03\x02\xE8\x93\x90\x80\xf1\x06\x00\x80\x00\x00\x03\x02\xE8\x93\x90\xf1\x06\x00\x80\xf1\x06\x00\x80\x00\x00\x03\x02\xE8\x93\x90\xf1',
                    b'\xf1\t\xff\x80\x07My Brio\x07\xf1\x16\xff\x80\x08\x00\x15\x00`\x00\x04\x00\x00\x00\x00\x00\x00My Brio\x00\x8d\xf1\r\xff\x80\x0b\x00\x00Mic -R tn\xbb\xf1\n\xff\x80\x0b\x00\x01Mic -L\xc2\xf1\n\xff\x80\x0b\x00\x02Mic -C\xca\xf1\x0c\xff\x80\x0b\x00\x03Mic -Lfe\xf5\xf1\x0b\xff\x80\x0b\x00\x04Mic -LsL\xf1\x0b\xff\x80\x0b\x00\x05Mic -RsE\xf1\n\xff\x80\x0b\x00\x06Mic 07\xcf\xf1\n\xff\x80\x0b\x00\x07Mic 08\xcd\xf1\n\xff\x80\x0b\x00\x08Mic 09\xcb\xf1\n\xff\x80\x0b\x00\tMic 10\xd2\xf1\x0b\xff\x80\x0b\x00\n9-1-004\x13\xf1\x0b\xff\x80\x0b\x00\x0b9-1-006\x10\xf1\n\xff\x80\x0b\x00\x0cMic 13\xcc\xf1\n\xff\x80\x0b\x00\rMic 14\xca\xf1\n\xff\x80\x0b\x00\x0eMic 15\xc8\xf1\n\xff\x80\x0b\x00\x0fMic 16\xc6\xf1\n\xff\x80\x0b\x00\x10Mic 17\xc4\xf1\r\xff\x80\x0b\x00\x11Mic 18 tn\xc0\xf1\x0c\xff\x80\x0b\x00\x12L 1F 19A\xb5\xf1\n\xff\x80\x0b\x00\x13Mic -R\xaa\xf1\n\xff\x80\x0b\x00\x14Mic 13\xc4\xf1\n\xff\x80\x0b\x00\x15Mic 14\xc2\xf1\x0c\xff\x80\x0b\x00\x16L 1F 23A\xb6\xf1\x0c\xff\x80\x0b\x00\x17L 1F 24A\xb4\xf1\x0c\xff\x80\x0b\x00\x18L 1F 25A\xb2\xf1\x0c\xff\x80\x0b\x00\x19L 1F 26A\xb0\xf1\x0c\xff\x80\x0b\x00\x1aL 1F 27A\xae\xf1\x0c\xff\x80\x0b\x00\x1bL 1F 28A\xac\xf1\x0c\xff\x80\x0b\x00\x1cL 1F 29A\xaa\xf1\x0c\xff\x80\x0b\x00\x1dL 1F 30A\xb1\xf1\x0c\xff\x80\x0b\x00\x1eL 1F 31A\xaf\xf1\x0c\xff\x80\x0b\x00\x1fL 1F 32A\xad\xf1\x0c\xff\x80\x0b\x00 L 1F 33A\xab\xf1\x0c\xff\x80\x0b\x00!L 1F 34A\xa9\xf1\x0c\xff\x80\x0b\x00"L 1F 35A\xa7\xf1\x0c\xff\x80\x0b\x00#L 1F 36A\xa5\xf1\n\xff\x80\x0b\x00$Mic 11\xb6\xf1\x0c\xff\x80\x0b\x00%L 1F  2B\xb9\xf1\x0c\xff\x80\x0b\x00&L 1F  3B\xb7\xf1\x0c\xff\x80\x0b\x00\'L 1F  4B\xb5\xf1\x0c\xff\x80\x0b\x00(L 1F  5B\xb3\xf1\x0c\xff\x80\x0b\x00)L 1F  6B\xb1\xf1\x0c\xff\x80\x0b\x00*L 1F  7B\xaf\xf1\x0c\xff\x80\x0b\x00+L 1F  8B\xad\xf1\x0c\xff\x80\x0b\x00,L 1F  9B\xab\xf1\x0c\xff\x80\x0b\x00-L 1F 10B\xa2\xf1\x0b\xff\x80\x0b\x00.9-1-005\xee\xf1\x0b\xff\x80\x0b\x00/9-1-007\xeb\xf1"\xff\x80\x0b\x000VCA MasterVCA MasterVCAMaster\x13\xf1\n\xff\x80\x0b\x001Mic 13\xa7\xf1\x0f\xff\x80\x0b\x002jhihojufydh\xa7\xf1\x1b\xff\x80\x0b\x00317B Direct Output -L tn\xd1\xf1\x0f\xff\x80\x0b\x004L 1F 17B tn\x92\xf1\n\xff\x80\x0b\x005Mic 10\xa6\xf1\x0b\xff\x80\x0b\x006Group 1\xe1\xf1\x0c\xff\x80\x0b\x007L 1F 20B\x97\xf1\n\xff\x80\x0b\x008Main 1g\xf1\x0f\xff\x80\x0b\x009L 1F 22B tn\x91\xf1\x0c\xff\x80\x0b\x00:fcfhggfd\x0c\xf1\n\xff\x80\x0b\x00;Main 3b\xf1\t\xff\x80\x0b\x00<Aux 1\xba\xf1\t\xff\x80\x0b\x00=Au', # example of random unsolicited message received:
                    ]

    # following test data created by encode - checksum is worng, but seems to pass checks in this script?
    test_data = [b'\xf1\x06\x00P\x00\x00\x03\x02\xe8\xc3', # message created by me - mixer refuses but I think valid
                    b'\xf1\x06\x00P\x00\x00\x03\x02\xe8\x93',# correct checksum for mixer - ithink invalid
                    b'\xf1\x06\x00\x80\x00\x00\x03\x02\xe8\xc3',#invalid
                    b'\xf1\x06\x00\x80\x00\x00\x03\x02\xe8\x93',# Valid and OK for mixer - its the P vs 80? - try bytearray instead of bytes??
                  ]

    # Valid messages split across two blocks of data
    test_data_split = [b'\xf1\x06\x00\x80\x00\x00\x03\x02\xE8\x93\xf1\x06\x00\x80\x00',
                        b'\x00\x03\x02\xE8\x93',
                        ]

    def test_unpack(test_data):
        print('test data:')
        print('data', test_data, '\n')

        extracted_data = unpack_data(test_data)

        print('messages extracted:')
        for message in extracted_data[0]:
            print(message)

        print ('number of messages extracted:', len(extracted_data[0]))

        print ('\nresidual data:', extracted_data[1])

    """
    for data in test_data:
        test_unpack(data)
        time.sleep(3)
    """
    test_unpack(test_data[3])

    """
    # test valid message split across two sets of data
    messages, residual = unpack_data(test_data_split[0])
    print(messages, residual)
    messages, residual = unpack_data(test_data_split[1], residual)
    print(messages, residual)
    """