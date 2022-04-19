# ConnectIO
# For testing SWP08/Probel router control - cross-point switching + label pushing
# Peter Walker, March 2022

# TODO, pass argument csv file name to test multiple patches
# TODO present returned messages better (ACK/NAK)
# deal with different matrix/level/multiplier etc

# prot ver 02 - print responses from router, cleanly in flow of user input rather than as they come in from Connection.
# todo - provide a version that outputs all response, including what we cant parse, and ACK/NAK
#      ... should really wait for ack and retry if none before sending next message.

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

    # - If more arguments supplied, concatenate into a label
    if len(r) > 2:
        label = " ".join(r[2:])
    else:
        label = False

    return int(source), int(destination), label


def get_received_messages(conn):
    while len(conn._messages):
        message = conn.get_message()
        print("Message Received:", message)


if __name__ == '__main__':
    # - Format & print header
    heading = "SWPO8 Router Control - Cross-point switching and label pushing"
    header_width = len(heading) + 8
    print("\n{}\n -- {} --\n{}".format(header_width * '#', heading, header_width * '-'))

    # - Get last used settings, and prompt user to accept or change
    settings = config.get_settings()
    # - Save user confirmed settings for next time
    config.save_settings(settings)

    # - Open a TCP connection with the router
    connection = Connection(settings["Router IP Address"], settings["Port"], settings["Protocol"])

    # - Wait for connection status to be Connected
    while connection.status != "Connected":
        pass

    # TODO - change to use 1 based input so user is entering same numbers as shown in Calrec UI/CSV
    print("\nNote, values are 0 based, (I.E. Calrec GUI/CSV values-1)")

    while True:
        if connection.status != "Connected":
            print("connection status:", connection.status)

        connection.flush_receive_buffer()
        source, destination, label = get_user_input()
        connect_msg = Message.connect(source, destination)

        print("Sending:", connect_msg)
        connection.send(connect_msg.encoded)

        if label:
            label_msg = Message.push_labels([label], destination, char_len=settings["Label Length"])
            print("Sending", label_msg)
            connection.send(label_msg.encoded)

        print("\nChecking for response from router...")
        get_received_messages(connection)
