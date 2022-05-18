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
import datetime
from string import punctuation  # - used just to parse/sanitise user input.

import cli_utils
import connectIO_cli_settings as config
from connection_02 import Connection
from swp_message_02 import Message
from swp_node_02 import Node


# Time to wait for ACK before retry.
TIMEOUT = 1
# Number of send/resend to attempt until ACK received
MAX_SEND_ATTEMPTS = 5

TITLE = "ConnectIO"
VERSION = 1.0


def format_timestamp(t):
    # takes a datetime.datetime object and returns as formatted string
    return t.strftime('%H:%M:%S.%f')[:-3]  # - truncated to millisecond / 3 decimal places on the seconds field.


def get_number(prompt='number'):
    """
    cli prompt user until they input a number
    :param prompt: optional string for the prompt to describe the number being asked for
    :return: int, from user input.
    """
    # - prompt user to input a number, repeat until they do and return the number as an int
    while True:
        n = input("Enter " + prompt + ": ").split()
        if len(n) == 1 and n[0].strip(punctuation).isnumeric():
            return int(n[0].strip(punctuation))


def prompt_matrix_level():
    ok = input("Matrix: 1, Level: 1 (y/n?): ")
    if ok.lower() in ("y", "yes", ""):
        return 0, 0
    else:
        mtx = get_number("matrix") - 1
        lvl = get_number("level") - 1
        return mtx, lvl


def prompt_for_tally_dump(matrix, level):
    confirm = input("Get current connection state for matrix {}, level {} (y/n)?".format(matrix + 1, level + 1))
    if confirm.lower() in ("y", "yes", ""):
        msg = Message.cross_point_tally_dump_request(matrix, level)
        print("DEBUG prompt for tally dump", msg, msg.summary)
        send_message(connection, msg)


def prompt_source_dest_label():
    while True:
        s = input("\nEnter source ID, destination ID & optional label: ").split()

        if len(s) > 1:
            if s[0].strip(punctuation).isnumeric() and s[1].strip(punctuation).isnumeric():
                # - get src/dest and offset gui/csv 1 based to protocol 0 based
                src = int(s[0].strip(punctuation)) - 1
                dest = int(s[1].strip(punctuation)) - 1
                if src >= 0 and dest >= 0:
                    if len(s) > 2:
                        # Concatenate remaining args into a single label
                        # (user supplied label with one or more spaces)
                        lbl = " ".join(s[2:])
                    else:
                        lbl = None

                    return src, dest, lbl


def send_message(connection, message):
    connection.flush_receive_buffer()

    ack = False
    tries = 0

    print("[" + format_timestamp(datetime.datetime.now()) + "] >>> Sending:",
          message.summary, ", Encoded:", message.encoded)

    connection.send(message)
    time.sleep(1)
    response = None
    # TODO PREVENT WAITING FOREVER, (TIMEOUT & RETRIES!)
    while not response:
        while connection.receive_buffer_len():
            timestamp, response = connection.get_message()
            response = Message.decode(response)

            print("[" + format_timestamp(timestamp) + "] <<< Received:",
                  response.summary,
                  ", Encoded:", response.encoded)


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)

    # - Get last used settings, and prompt user to accept or change
    # - Note my router is 192.169.1.201
    settings = config.get_settings()
    # - Save user confirmed settings for next time
    config.save_settings(settings)

    # - Open a TCP client connection with the router
    connection = Connection(settings["Router IP Address"], settings["Port"], settings["Protocol"])

    # - Wait for connection status to be Connected
    while connection.status != "Connected":
        pass

    matrix, level = prompt_matrix_level()
    prompt_for_tally_dump(matrix, level)

    while True:
        # - Check connection and wait for reconnect if down
        while connection.status != "Connected":
            print("connection status:", connection.status)

        source_id, destination_id, label = prompt_source_dest_label()
        source = Node(matrix, level, source_id, "source")
        destination = Node(matrix, level, destination_id, "destination")

        patch_msg = Message.connect(source, destination)
        send_message(connection, patch_msg)

        if label:
            label_msg = Message.push_labels([label], destination, char_len=settings["Label Length"])
            send_message(connection, label_msg)

        prompt_for_tally_dump(matrix, level)