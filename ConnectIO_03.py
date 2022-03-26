# SWP08 / Probel controller

# SWP08 protocol info:
# https://wwwapps.grassvalley.com/docs/Manuals/sam/Protocols%20and%20MIBs/Router%20Control%20Protocols%20SW-P-88%20Issue%204b.pdf

import time

from connection_01 import Connection
from swp08_01 import Message

import swp_utils_01 as utils


def convert_string(s):
    """
    convert a string to a list of ascii values
    :param s: str
    :return: list
    """
    r = list(s)
    for i, l in enumerate(r):
        r[i] = ord(l)
    return r


def push_labels(labels):
    # page 77 of issue32 spec
    #command1 = 0x6b  # 107 dec
    #command2 = 0xeb  # 235 dec

    CMD = 235
    CMD = 107

    matrix = 0
    name_len = 0  # 4 char label # TODO - try 00, 01, 02, 03, 04 (different message length formats but 0 should be 4 char)
    start_dest_div = 0 #/ 256 #  .. # OK, THIS IS NOW WORKING, BUT NEED DESTINATIONS WITH LOW IDs, NEED TO FIX THE DIV/MOD
    start_dest_mod = 0 #% 256
    qty_names = 4

    # TODO - NOTE, LABELS MUST BE OF THE EXPECTED LENGTH
    name1 = convert_string(labels[0])
    name2 = convert_string(labels[1])
    name3 = convert_string(labels[2])
    name4 = convert_string(labels[3])




    data = [CMD] + [matrix, name_len, start_dest_div, start_dest_mod, qty_names] + name1 + name2 + name3 + name4
    print("debug data", data)
    byte_count = len(data)
    #print("DEBUG byte count:", byte_count)
    data.append(byte_count)
    checksum = utils.calculate_checksum(data)
    #checksum = 4 # debug check I get a NAK... get nothing back

    message = utils.SOM + data + [checksum] + utils.EOM
    print("DEBUG label message", message)
    print("BEBUG BYTES", bytes(message))
    return bytes(message)


def push_labels2():
    # page 77 of issue32 spec
    #command1 = 0x6b  # 107 dec
    #command2 = 0xeb  # 235 dec

    CMD = 107
    matrix = 0
    name_len = 0  # 4 char label
    start_dest_div = 0 #/ 256
    start_dest_mod = 0 #% 256
    qty_names = 3
    name1 = [97,97,97,97]
    name2 = [97, 97, 97, 97 ]
    name3 = [97, 97, 97, 97 ]
    name4 = [97, 97, 97, 97 ]
    data  = [CMD] + [matrix, name_len, start_dest_div, start_dest_mod, qty_names] + name1 + name2 + name3 + name4

    byte_count = len(data)
    #print("DEBUG byte count:", byte_count)
    data.append(byte_count)
    checksum = utils.calculate_checksum(data)

    message = utils.SOM + data + [checksum] + utils.EOM
    #print("DEBUG message", message)
    return bytes(message)


if __name__ == '__main__':

    print(20 * '#' + ' ConnectIO - SWP08 router controller ' + 20 * '#')

    #address = "172.29.1.24"     # Impulse default Router Management adapaptor
    address = "192.169.1.201"    # Impulse added address for Router on Interface 3
    port = 61000  # Fixed port for SWP08

    # Open a TCP connection with the mixer/router
    connection = Connection(address, port, "SWP08")

    # - Wait for connection status to be Connected
    while connection.status == "Starting":
        pass
        print(connection.status)
    time.sleep(4)
    print(connection.status)
    # Test message - connect source 0 to destination 10
    test1 = Message.connect(20, 0)
    test2 = Message.connect(21, 1)
    test3 = Message.connect(22, 2)
    test4 = Message.connect(23, 3)

    #DISCONNECTS, mute source in configure set to 100, so 99 here...
    # THESE ARE NOT WORKING, NO OUTPUT INT THE ROUTER TELNET FOR THESE EITHER.
    #dis1 = Message.connect(100, 0)
    #dis2 = Message.connect(100, 2)
    #dis3 = Message.connect(99, 3)
    #dis4 = Message.connect(99, 4)


    #print("Test message:", test1)
    #print("Test message:", test2)
    #print("Test message:", test3)
    #print("Test message:", test4)

    # Sample message from mixer - Connected
    #test_message = b'\x10\x02\x04\x00\x00\n\x00\x05\xed\x10\x03'
    #test2 = Message.decode(test_message)
    #print("Test decoding:", test2)


    print("sending connections")
    connection.send(test1._encoded)
    connection.send(test2._encoded)
    connection.send(test3._encoded)
    connection.send(test4._encoded)

    #connection.send(dis1)
    #connection.send(dis2)
    #connection.send(dis3)
    #connection.send(dis4)



    time.sleep(2)
    print("pushing labels")

    labels = ["ones", "twos", "thre", "four"]
    labels2 = ["pete", "test", "help", "zXXX"]

    #label_message = push_labels(labels)
    #connection.send(label_message)

    time.sleep(2)
    #label_message = push_labels(labels2)
    #connection.send(label_message)



    i = 0
    while True:
        #print('\n', i, 'qty:', len(connection._messages), 'residual data', connection._residual_data)
        #connection.send(label_message)
        message = connection.get_message()
        if message:
            print("message recieved:")
            print(message)
            print ("len", len(message))
            for ch in message:
                print(ch, end=" - ")
            print(Message.decode(message))

            i += 1



