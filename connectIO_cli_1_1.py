# - ConnectIO CLI
# - CLI interface for For testing the sending of SWP08/Probel control messages to a router,
# - making connections, pushing labels and requesting connection/tally data.

# Peter Walker, March 2022

import time
import datetime
from string import punctuation

# - Local modules
import cli_utils
import connectIO_cli_settings as config
from connection_02 import Connection
import swp_message_03 as swp_message
from swp_node_03 import Node
import swp_utils_02 as swp_utils


# Time to wait for ACK before retry.
TIMEOUT = 1
# Number of send/resend to attempt until ACK received
MAX_SEND_ATTEMPTS = 5

TITLE = "ConnectIO"
VERSION = 1.1


def format_timestamp(t):
    # takes a datetime.datetime object and returns as formatted string
    # TODO - DEPREACTED, MOVED TO SWP_UTILS
    return t.strftime('%H:%M:%S.%f')[:-3]  # - truncated to millisecond / 3 decimal places on the seconds field.


def prompt_matrix_level():
    ok = input("Matrix: 1, Level: 1 (y/n?): ")
    if ok.lower() in ("y", "yes", ""):
        return 0, 0
    else:
        matrix = cli_utils.get_number("matrix") - 1
        level = cli_utils.get_number("level") - 1
        return matrix, level


def prompt_for_tally_dump(matrix, level):
    confirm = input("Get current connection state for matrix {}, level {} (y/n)?".format(matrix + 1, level + 1))
    if confirm.lower() in ("y", "yes", ""):
        msg = swp_message.GetConnections(matrix, level)
        send_message(connection, msg)


def prompt_source_dest_label():
    while True:
        s = input("\nEnter source ID, destination ID & optional label "
                  "(or press Enter to check received message buffer): ").split()
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

        elif len(s) == 0:
            # - User hit enter without input, print any messages received from router since last send.
            return None, None, None


def get_received_messages(conn):
    if not conn.receive_buffer_len():
        print("Received message buffer is empty")
    else:
        while conn.receive_buffer_len():
            timestamp, response = conn.get_message()
            response = swp_message.decode(response)
            cli_utils.print_block("[" + format_timestamp(timestamp) + "] <<< Received:",
                                  [response.__str__(), "Encoded: " + str(response.encoded)])


def send_message(conn, msg):
    """
    :param conn: connection object
    :param msg: swp_message object
    :return:
    """
    conn.flush_receive_buffer()

    ack = False
    tries = 0

    #cli_utils.print_block("[" + format_timestamp(datetime.datetime.now()) + "] >>> Sending:",
    #                      [msg.__str__(), "Encoded: " + str(msg.encoded)])

    swp_utils.print_message(datetime.datetime.now(), "sending", msg)

    conn.send(msg)
    t = time.time()
    ts = 0  # - timer
    response = None
    # TODO Retry after timeout, check for ACK
    while ts < TIMEOUT:
        ts = time.time() - t
        while conn.receive_buffer_len():
            timestamp, response = conn.get_message()
            response = swp_message.decode(response)

            #cli_utils.print_block("[" + format_timestamp(timestamp) + "] <<< Received:",
            #                      [response.__str__(), "Encoded: " + str(response.encoded)])
            swp_utils.print_message(timestamp, "received", swp_message)

    if not response:
        print("Timeout, no response from router after {}s".format(TIMEOUT))


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

    mtx, lvl = prompt_matrix_level()
    prompt_for_tally_dump(mtx, lvl)

    while True:
        # - Check connection and wait for reconnect if down
        while connection.status != "Connected":
            print("connection status:", connection.status)

        source_id, destination_id, label = prompt_source_dest_label()

        if source_id is None:
            get_received_messages(connection)
        else:
            source = Node(mtx, lvl, source_id, "source")
            destination = Node(mtx, lvl, destination_id, "destination")

            patch_msg = swp_message.Connect(source, destination)
            send_message(connection, patch_msg)

            if label:
                label_msg = swp_message.PushLabels(destination, [label], matrix=mtx, char_len=settings["Label Length"])
                send_message(connection, label_msg)

        prompt_for_tally_dump(mtx, lvl)
