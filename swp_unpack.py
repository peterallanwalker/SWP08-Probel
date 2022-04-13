# SWP08 unpack 
# Identifies, validates and Extracts SWP08 messages from byte strings
# Peter Walker, June 2021.

# Version 2:
# Extracts ACK & NAK messages as well as SOM+DATA+EOM messages that have been validated with checksum
# and handles residual data / messages split over two receive chunks


import swp_utils as utils
from swp_utils import is_checksum_valid


def _check_dle(data, index):
    # TODO should prevent indexing > len(data).. though doing that before calling this function
    if data[index] != utils.DLE:
        return "NOT DLE!"
    if data[index + 1] == utils.ACK[1]:
        return "ACK"
    if data[index + 1] == utils.NAK[1]:
        return "NAK"
    if data[index + 1] == utils.SOM[1]:
        return "SOM"
    if data[index + 1] == utils.EOM[1]:
        return "EOM"
    if data[index + 1] == utils.DLE:
        # DLE DLE - ("escaped"/double DLE - payload value not header)
        return "ESCAPED DLE / PAYLOAD VALUE"

    # Should never see this, DLE should either be part of ACK/NAK/SOM/EOM or escaped (DLE DLE) payload value
    return "LONE DLE!"


def _escape_dles(message):
    """
    Takes a byte string representing a message - SOM + DATA + EOM (SOM & EOM are required)
    and replaces any instances of DLE DLE found within the payload with a single DLE
    :param message: byte string representing SOM + DATA + EOM
    :return: byte sting with DLE DLE replaced with DLE
    """
    r = message[2: -2]  # - Strip SOM & EOM
    r = r.replace(bytes([utils.DLE, utils.DLE]), bytes([utils.DLE]))
    return bytes(utils.SOM) + r + bytes(utils.EOM)

    """
    r = []
    i = 0
    while i < len(message) - 1:
        if message[i] == utils.DLE and message[i + 1] == utils.DLE:
            i += 1  # - skip first DLE
        r.append(message[i])
        i += 1
    r.append(message[-1])  # - Add last byte
    return bytes(r)
    """


def unpack_data(data, previous_insufficient_data=False):
    """ Takes bytes, (and any residual bytes returned from previous call).
        Extracts and returns valid SWP08 messages found within
        also returns any residual data from the end that could be the beginning of a valid message
        (with remainder of message in next bytes to be received - to supply back to this function in next call)

    :param data: bytes
    :param previous_insufficient_data: bytes (possible start of message from preceding data)
    :return: bytes, bytes or bool (extracted messages, residual data that may be beginning of message who's remainder
                is due in next received data, or false if no residual data.
    """

    if previous_insufficient_data:
        data = previous_insufficient_data + data

    messages = []
    insufficient_data = False

    # - DEBUG - #
    #print("\n[swp_unpack.unpack_data]: DATA DUMP - ", data)

    while len(data) > 0:
        # - First index within data containing a SWP DLE value
        next_dle = data.find(utils.DLE)

        if next_dle == -1:
            # - No more potential messages headers in remaining data
            #print("[swp_unpack.unpack_data]: No headers found in", data)
            break

        #print("[swp_unpack.unpack_data]: Checking data len: {} data: {}".format(len(data), data))
        #print("[swp_unpack.unpack_data]: dle found at index {}".format(next_dle))

        if next_dle == len(data) - 1:
            # next dle is last byte in the remaining data
            insufficient_data = data[next_dle:]
            #print("[swp_unpack.unpack_data]: DLE found in last byte, appending for next call")
            break

        dle_type = _check_dle(data, next_dle)
        #print("[swp_unpack.unpack_data]: DLE type:", dle_type)
        if dle_type == "ACK" or dle_type == "NAK":
            #print("[swp_unpack.unpack_data]: ACK/NAK processed, ({} received)".format(dle_type))
            messages.append(data[next_dle: next_dle + 2])  # the two bytes comprising the ACK/NAK message
            data = data[next_dle + 2:]  # remove the ACK/NAK for next pass

        elif dle_type == "EOM":
            #print("[swp_unpack.unpack_data]: EOM found outside of SOM check (message probably already processed)")
            data = data[next_dle + 2:]  # remove the EOM for next pass

        elif dle_type == "ESCAPED DLE / PAYLOAD VALUE":
            # - Skip, escaped DLEs will be cleaned as part of SOM+DATA+EOM extraction
            data = data[next_dle + 1:]

        elif dle_type == "LONE DLE!":
            data = data[next_dle + 1:]  # - Ignore lone DLE

        elif dle_type == "SOM":

            # - TODO - if message payload contains false EOM, eg. connect destination 16 to source 3 (\x16\x03)
            #           then it is not currently being parsed
            #print("[swp_unpack.unpack_data]: SOM found, looking for EOM...")
            eom_index = data.find(bytes([utils.EOM[0], utils.EOM[1]]))

            #print("[swp_unpack.unpack_data]: eom index", eom_index, data[eom_index])
            if eom_index != -1:
                #print("[swp_unpack.unpack_data]: SOM + DATA + EOM:", data[next_dle: eom_index + 2])
                msg = data[next_dle: eom_index + 2]
                msg = _escape_dles(msg)

                if is_checksum_valid(msg):
                    messages.append(msg)
                    #data = data[next_dle + 2:]  # - Just strips SOM
                    data = data[eom_index:]  # - strips whole validated SOM+DATA+EOM
                else:
                    # Message not validated, so just strip SOM so remainder can be checked for
                    # further SOM within the invalid payload.
                    data = data[next_dle + 2:]

            else:
                #print("[swp_unpack.unpack_data]: SOM found without an EOM")
                # - Adding 2 as next DLE has returned -1 and we want to skip + 1
                # ... though arguably we should break here and pass all remaining data to insufficient..
                # that would stop us searching rest of data for valid messages until next chunk received though.
                # ... not doing so will lose this potential SOM if there is further insufficient data though
                insufficient_data = data[next_dle:]
                data = data[next_dle + 2:]
                #break

    return messages, insufficient_data


def test_1():
    ack = b'\x10\x06'
    nak = b'\x10\x15'
    res = b'\x01'
    dle = b'\x10'

    data = res + ack + nak + res + dle
    messages, residual_data = unpack_data(data)
    print("[swp_unpack test 1]: test data -", data)
    print("[swp_unpack test 1]: extracted messages -", messages)
    print("[swp_unpack test 1]: residual data -", residual_data)
    if messages == [ack, nak] and residual_data == dle:
        print("test 1 - PASS")
    else:
        print("TEST 1 - FAIL")


def test_2():
    ack = b'\x10\x06'
    nak = b'\x10\x15'
    res = b'\x01'
    dle = b'\x10'
    som = b'\x10\x02'

    data = res + ack + nak + res + dle
    messages, residual_data = unpack_data(data)
    print("[swp_unpack test 1]: test data -", data)
    print("[swp_unpack test 1]: extracted messages -", messages)
    print("[swp_unpack test 1]: residual data -", residual_data)

    ack_end = b'\x06'
    messages, residual_data = unpack_data(ack_end, residual_data)

    print("[swp_unpack test 1]: extracted messages -", messages)
    print("[swp_unpack test 1]: residual data -", residual_data)

    if messages == [ack] and not residual_data:
        print("TEST 2 PASS")
    else:
        print("TEST 2 FAIL")


def test_3():
    test_data = b'\x01\x10\x02\x01\x01'
    messages, residual_data = unpack_data(test_data)
    print("messages:", messages)
    print("residual data:", residual_data)
    if messages == [] and residual_data == test_data[1:]:
        print("TEST 3: PASS")
    else:
        print("TEST 3: FAIL")


def test_4():
    # 2 x valid messages in one string
    test_data = b'\x10\x02\x04\x00\x00\x0c\x02\x05\xe9\x10\x03\x10\x02\x04\x00\x00\r\x03\x05\xe7\x10\x03'
    # - short non-SWP messages but valid SOM/EOM
    msg1 = b'\x10\x02\x01\x10\x03'
    msg2 = b'\x10\x02\x01\x02\x03\x10\x03'

    messages, residual_data = unpack_data(test_data + msg1 + msg2)
    #messages, residual_data = unpack_data(test_data)
    #messages, residual_data = unpack_data(msg1 + msg2)
    print("messages:", messages)
    print("residual data:", residual_data)

    res1 = b'\x10\x02\x04\x00\x00\x0c\x02\x05\xe9\x10\x03'
    res2 = b'\x10\x02\x04\x00\x00\r\x03\x05\xe7\x10\x03'
    if messages == [res1, res2, msg1, msg2] and not residual_data:
        print("TEST 4: PASS")
    else:
        print("TEST 4: FAIL")


def test_5():

    # - False SOM followed by valid SOM/EOM - should be extracted as 2 messages the full sting
    # b'\x10\x02\x01\x02\x10\x02\x01\x10\x03'
    # and the second message within b'\x10\x02\x01\x10\x03'
    msg3 = b'\x10\x02\x01\x02\x10\x02\x01\x10\x03'
    messages, residual_data = unpack_data(msg3)
    print("messages:", messages)
    print("residual data:", residual_data)

    if messages == [b'\x10\x02\x01\x02\x10\x02\x01\x10\x03', b'\x10\x02\x01\x10\x03'] \
            and not residual_data:
        print("TEST 5: PASS")
    else:
        print("TEST 5: FAIL")


def test_6():
    som = b'\x10\x02'
    eom = b'\x10\x03'
    data = b'\x01\x02\x03'
    msg = som + data + eom
    messages, residual_data = unpack_data(msg)
    print(messages)
    print(residual_data)


def test_7():
    msg1 = b'\x10\x06\x10\x02\x04\x00\x00\x00\n\x05\xed\x10\x03\x10\x06\x10\x06\x10\x06\x10\x06\x10\x06\x10\x06\x10' \
           b'\x06\x10\x06\x10\x06\x10\x02\x04\x00\x00\x01\x0b\x05\xeb\x10\x03\x10\x02\x04\x00\x00\x02\x0c\x05\xe9\x10' \
           b'\x03\x10\x02\x04\x00\x00\x03\r\x05\xe7\x10\x03\x10\x02\x04\x00\x00\x04\x0e\x05\xe5\x10\x03\x10\x02\x04' \
           b'\x00\x00\x05\x0f\x05\xe3\x10\x03\x10\x02\x04\x00\x00\x06\x10\x10\x05\xe1\x10\x03\x10\x02\x04\x00\x00\x07' \
           b'\x11\x05\xdf\x10\x03\x10\x02\x04\x00\x00\x08\x12\x05\xdd\x10\x03\x10\x02\x04\x00\x00\t\x13\x05\xdb\x10' \
           b'\x03 '

    msg2 = b'\x10\x06\x10\x02\x04\x00\x00\x00\n\x05\xed\x10\x03\x10\x06\x10\x06\x10\x06\x10\x06\x10\x06\x10\x06\x10' \
           b'\x06\x10\x06\x10\x06\x10\x02\x04\x00\x00\x01\x0b\x05\xeb\x10\x03\x10\x02\x04\x00\x00\x02\x0c\x05\xe9\x10' \
           b'\x03\x10\x02\x04\x00\x00\x03\r\x05\xe7\x10\x03\x10\x02\x04\x00\x00\x04\x0e\x05\xe5\x10\x03\x10\x02\x04'

    msg3 = b'\x00\x00\x05\x0f\x05\xe3\x10\x03\x10\x02\x04\x00\x00\x06\x10\x10\x05\xe1\x10\x03\x10\x02\x04\x00\x00\x07' \
           b'\x11\x05\xdf\x10\x03\x10\x02\x04\x00\x00\x08\x12\x05\xdd\x10\x03\x10\x02\x04\x00\x00\t\x13\x05\xdb\x10' \
           b'\x03 '

    messages, residual_data = unpack_data(msg1)
    messages2, residual_data2 = unpack_data(msg2)
    messages3, residual_data3 = unpack_data(msg3, residual_data2)

    for msg in messages:
        print(msg)
    print(residual_data)
    print(len(messages), "messages unpacked")
    print(40*'-')

    for msg in messages2:
        print(msg)
    print(residual_data2)
    print(len(messages2), "messages unpacked")
    print(40 * '-')
    for msg in messages3:
        print(msg)
    print(residual_data3)
    print(len(messages3), "messages unpacked")


def test_8():
    data = b''
    msg = b'\x10\x02\x04\x00\x00\x00\n\x05\xed\x10\x03'
    msg = b'\x10\x02\x04\x00\x00\x0c\x02\x05\xe9\x10\x03'
    msg = b'\x10\x02\x04\x00\x00\r\x03\x05\xe7\x10\x03'
    valid = is_checksum_valid(msg)
    print(valid)


def test_9():
    chunk1 = b'\x10\x06\x10\x02\x04\x00\x00\x00\n\x05\xed\x10\x03\x10\x06\x10\x06\x10\x06\x10\x06\x10\x06\x10\x06\x10' \
             b'\x06\x10\x06\x10\x06\x10\x02\x04\x00\x00\x01\x0b\x05\xeb\x10\x03\x10\x02\x04\x00\x00\x02\x0c\x05\xe9\x10' \
             b'\x03\x10\x02\x04\x00\x00\x03\r\x05\xe7\x10\x03\x10\x02\x04\x00\x00\x04\x0e\x05\xe5\x10\x03\x10\x02\x04'

    chunk2 = b'\x00\x00\x05\x0f\x05\xe3\x10\x03\x10\x02\x04\x00\x00\x06\x10\x10\x05\xe1\x10\x03\x10\x02\x04\x00\x00\x07' \
             b'\x11\x05\xdf\x10\x03\x10\x02\x04\x00\x00\x08\x12\x05\xdd\x10\x03\x10\x02\x04\x00\x00\t\x13\x05\xdb\x10' \
             b'\x03 '

    messages1, residual_data1 = unpack_data(chunk1)
    messages2, residual_data2 = unpack_data(chunk2, residual_data1)

    for msg in messages1:

        if msg not in (bytes(utils.ACK), bytes(utils.NAK)):
            print(msg, is_checksum_valid(msg))
        else:
            print(msg)

    print(residual_data1)
    print(len(messages1), "messages unpacked")
    print(40 * '-')

    for msg in messages2:
        print(msg, is_checksum_valid(msg))

    print(residual_data2)
    print(len(messages2), "messages unpacked")
    if len(messages1) == 15 and len(messages2) == 5:
        print("TEST 9: PASS")
    else:
        print("TEST 9: FAIL")


def test_escaped_dles():
    som = b'\x10\x02'
    eom = b'\x10\x03'
    data = b'\x01\x01\x01\x10\x10\x01'
    data = b'\x01\x01\x01\x10\x10\x10\x10\x01'

    msg = som + data + eom
    print("test escaped, msg:", msg)
    print("escaped", _escape_dles(msg))


def test_valid_invalid():
    ack = b'\x10\x06'
    valid = b'\x10\x02\x04\x00\x00\x00\n\x05\xed\x10\x03'
    invalid = b'\x10\x02\x04\x00\x00\x01\x00\n\x05\xed\x10\x03'
    data = ack + valid + invalid
    data, residual_data = unpack_data(data)
    for msg in data:
        print(msg)


def debug_failed_message():
    # - failing to parse this connect message, 3 - 16... 16 is DLE!
    # ... so source & dest gets encoded as \x10\x03 ... which is the same as EOM
    # ... but unpack should fail to validate it as EOM by checksum and continue to look for DLE... but is not working.
    # ... also, if in message encode I escape the dle, so pass \x10\x10\x03 then unpack should escape it and handle.
    # ... check how I', unpckaing/escaping
    failed_message = b'\x10\x02\x02\x00\x00\x10\x03\x05\xe6\x10\x03'

    failed_message = b'\x10\x02\x02\x00\x00\x10\x10\x03\x05\xe6\x10\x03'
    print("orig", failed_message)
    print("escaped", _escape_dles(failed_message))
    data, residual_data = unpack_data(failed_message)
    print("data", data)
    print("residual", residual_data)


if __name__ == '__main__':
    #test_1()
    #test_2()
    #test_3()
    #test_4()
    #test_5()
    #test_6()
    #test_7()
    #test_8()
    #test_9()
    #test_escaped_dles()
    #test_valid_invalid()
    debug_failed_message()
