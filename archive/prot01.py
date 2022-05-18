# SWP08 / Probel controller

# SWP08 protocol info:
# https://wwwapps.grassvalley.com/docs/Manuals/sam/Protocols%20and%20MIBs/Router%20Control%20Protocols%20SW-P-88%20Issue%204b.pdf

# Figure out proper DLE handling
# page 10 of protocol doc
# currently, I expect messages containing DLE - \x10 dec 16 will fail
# need to check for DLEDLE in payload to differentiate from DLE in header (and convert DLEDLE payload to DLE
# and when packing, convert DLE payload values to DLEDLE (after bytecount & checksum... check doc)


# - TEST BY SENDING PAY load containing 16
# - switch source/dest 16 on mixer and see how I handle the connected messages
#  (and save the output from the mixer so I can test fixing it offline )


from archive.connection import Connection
from swp_message import Message

if __name__ == '__main__':

    print(20 * '#' + ' ConnectIO - SWP08 router controller ' + 20 * '#')

    #address = "172.29.1.24"     # Impulse default Router Management adapaptor
    address = "192.169.1.201"    # Impulse added address for Router on Interface 3
    port = 61000  # Fixed port for SWP08

    # Open a TCP connection with the mixer/router
    connection = Connection(address, port, "SWP08")

    # - Wait for connection status to be Connected
    while connection.status != "Connected":
        pass

    # - Test message - connect source 0 to destination 10
    test1 = Message.connect(10, 0)
    connection.send(test1.encoded)

    test2 = Message.connect(11, 1)
    connection.send(test2.encoded)

    test3 = Message.connect(12, 2)
    connection.send(test3.encoded)

    test4 = Message.connect(13, 3)
    connection.send(test4.encoded)

    test5 = Message.connect(14, 4)
    connection.send(test5.encoded)

    test6 = Message.connect(15, 5)
    connection.send(test6.encoded)

    # expect this to fail as 16 = DLE... but it didn't!
    # - mixer handles the message I send
    # - But I am failing to parse the returned message
    test7 = Message.connect(16, 6)
    connection.send(test7.encoded)

    test8 = Message.connect(17, 7)
    connection.send(test8.encoded)

    test9 = Message.connect(18, 8)
    connection.send(test9.encoded)

    test10 = Message.connect(19, 9)
    connection.send(test10.encoded)



    i = 0

    print("\nEXTRACTED MESSAGES:")
    while True:

        message = connection.get_message()
        if message:
            print("message recieved:")
            print(message)
            print ("len", len(message))
            for ch in message:
                print(ch, end=" - ")
            print(Message.decode(message))

            i += 1



