# ConnectIO
# For testing SWP08/Probel router control - cross-point switching + label pushing
# Peter Walker, March 2022

# - TODO, pass argument csv file name to test multiple patches?
# TODO provide option for longer labels (perhaps as part of settings)
# TODO present returned messaegs better (ACK/NAK)
# provide option to pass a CSV to test multiple patches
# deal with different matrix/level/multiplier etc
# sort labels div/mod else wont work with IDs > 10?
# option to send lots of labels

import time

from string import punctuation  # - used just to parse/sanitise user input.

import connection_settings as config
from connection import Connection
from swp_message import Message


def get_user_input():
    r = input("\nEnter source, destination & optional label: ")
    r = r.split()
    invalid_input_response = (-1, -1, False)

    if len(r) < 2:
        print("Not enough values passed")
        return invalid_input_response

    source = r[0].strip(punctuation)
    destination = r[1].strip(punctuation)

    if not source.isnumeric() or not destination.isnumeric():
        print("Source and destination values need to be numbers")
        return invalid_input_response

    if len(r) > 2:
        label = " ".join(r[2:])
    else:
        label = False

    return int(source), int(destination), label


def get_incoming_message(conn):
    message = conn.get_message()
    while message:
        #print("Message Recieved", Message.decode(message))
        print("Message Recieved", message)
        message = conn.get_message()

if __name__ == '__main__':
    # - Format & print header
    heading = "SWPO8 Router Control - Cross-point switching and label pushing"
    header_width = len(heading) + 8
    print("\n{}\n -- {} --\n{}".format(header_width * '#', heading, header_width * '-'))

    # - Get last used IP address, and prompt user accept/change
    settings = config.get_settings()
    # - Save user confirmed settings for next time
    config.save_settings(settings)

    # - Open a TCP connection with the router
    connection = Connection(settings["Router IP Address"], settings["Port"], settings["Protocol"])
    #connection = Connection(settings["Router IP Address"], settings["Port"], "SWP08")

    # - Wait for connection status to be Connected
    print("Waiting for connection...")
    while connection.status != "Connected":
        pass

    print("Note, values are 0 based, (I.E. Calrec GUI/CSV values-1)")

    while True:
        if connection.status != "connected":
            print(connection.status)
        source, destination, label = get_user_input()
        patch_msg = Message.connect(source, destination)
        print("Sending", patch_msg)
        connection.send(patch_msg.encoded)
        #get_incoming_message(connection)
        #time.sleep(2)  # messages failing sometimes.. maybe wait for NAK
        if label:
            label_msg = Message.push_labels([label], destination, char_len=settings["Label Length"])
            print("Sending", label_msg)
            connection.send(label_msg.encoded)
            #get_incoming_message(connection)
        print("\n")
