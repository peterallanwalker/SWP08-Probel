# ConnectIO
# For testing SWP08/Probel router control - cross-point switching + label pushing
# Peter Walker, March 2022

# TODO, pass argument csv file name to test multiple patches
# TODO present returned messages better (ACK/NAK)
# deal with different matrix/level/multiplier etc

# Testing - Connection currently using unpack 2 so we should
# be able to pull ACK/NAK from received message buffer
# TODO sort init for unknown messages and better handling/print of ACK/NAK
# ... maybe provide a print summary
# TODO, wait for ACK before sending next, retry if no ACK or NAK?


import time

from string import punctuation  # - used just to parse/sanitise user input.

import connection_settings as config
from connection import Connection
from swp_message import Message
import cli_utils

# Time to wait for ACK before retry.
TIMEOUT = 1
# Number of send/resend to attempt until ACK received
MAX_SEND_ATTEMPTS = 5

TITLE = "ConnectIO"
VERSION = 0.2


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


def send_message(connection, message):
    connection.flush_receive_buffer()

    ack = False
    tries = 0
    #while tries < MAX_SEND_ATTEMPTS or not ack:
        #connection.send(message.encoded)
        #tries += 1
        #t = time.time()
        #t2 = time.time()
        #response = False
        #while t2 < t + TIMEOUT:
        #    print(t2)
        #    response = connection.receive()
        #    t2 = time.time()

        #if response:
        #    response = Message.decode(response)
        #    print("Message received from router:", response)
        #    if response.command == "ACK":
        #        ack = True
        #        print("ACK received")
        #    else:
        #        print(Message.decode(response))

    message.print_summary("Sending >>>")
    connection.send(message.encoded)

    # TODO should retry until response but seems to be working instantly at the moment

    response = None
    # TODO PREVENT WAITING FOREVER, (TIMEOUT & RETRIES)
    while not response:
        while len(connection._messages):
            response = connection.get_message()
            response = Message.decode(response)

            if response.command == "ACK":
                print(" >>> ACK received")
            elif response.command == "NAK":
                print(" >>> ** NAK ** received!")
            else:
                response.print_summary(">>> Received Message:")
                #print("Message received "
                #      "from router:", response)


def get_received_messages(conn):

    while len(connection._messages):
        message = conn.get_message()
        #print("Message Recieved", Message.decode(message))
        print("Message Received:", message)


if __name__ == '__main__':

    cli_utils.print_header(TITLE, VERSION)

    # - Get last used settings, and prompt user to accept or change
    # - Note my router is 192.169.1.201
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
        while connection.status != "Connected":
            # TODO: put a timer in and print every n secs
            print("connection status:", connection.status)

        source, destination, label = get_user_input()

        patch_msg = Message.connect(source, destination)

        #print("Sending:", patch_msg)
        #cli_utils.print_block("Sending...", patch_msg.summary)
        #patch_msg.print_summary("Sending >>>")
        #connection.send(patch_msg.encoded)
        send_message(connection, patch_msg)

        if label:
            label_msg = Message.push_labels([label], destination, char_len=settings["Label Length"])
            #print("Sending", label_msg)
            #label_msg.print_summary("Sending >>>")
            #connection.send(label_msg.encoded)
            send_message(connection, label_msg)
            #get_received_messages(connection)
        print("\n")
