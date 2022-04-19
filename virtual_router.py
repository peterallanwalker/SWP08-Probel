#!/usr/bin/env python3
#
# Virtual router for testing SWP exchange when no router available
# Peter Walker April 2022.
#
# - ... Actually just a simple server listening for SWP08 messages
# - validates messages with checksum and replies with ACK for valid or NAK for invalid messages received.
# - On receipt of a "Connect" message will also reply back with a Connect message.
# - TODO, should really respond to a Connect message with a Connected message to properly emulate a router.
# - TODO, add support for other message types if when adding them to swp_message/connectIO to help debug/test
#
# Ref for working with sockets: https://realpython.com/python-sockets/


import socket
import threading
import time

from swp_message import Message
from swp_unpack import unpack_data
import swp_utils
import cli_utils

TITLE = "Virtual Router"
VERSION = 0.1
SWP_PORT = 61000


class SwpServer:
    """
    Server-side socket connection for comms with swp controller apps
    """
    def __init__(self, ip_address, port):
        self.address = ip_address
        self.port = port
        self.messages = []  # - For storing received messages

        # - To store any residual data containing SOM headers at the end of a received chunk without EOM
        # - that could potentially be the beginning of a valid message with the end due in the next chunk
        self.residual_data = False

        # - Set up to receive messages in a separate thread
        self.receiver = threading.Thread(target=self._run)
        self.receiver.daemon = True  # - Can't remember, think I need this to be able to quit.stop thread with control+c
        self.receiver.start()  # - Starts the thread, calling the target (_run())
        self.connection = False

    def _run(self):
        """ Called by self.receiver.start on initialisation """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.address, self.port))
            while True:
                s.listen()
                self.connection, addr = s.accept()
                with self.connection:

                    print('New connection with client:', addr, self.connection)
                    data = self.connection.recv(1024)  # - Receive up to 1MB of data
                    while data:
                        print("[virtual_router.run]: data received", data)
                        msgs, residual_data = unpack_data(data)
                        # TODO - just do self.messages += msgs rather than looping and appending each one at a time!
                        for msg in msgs:
                            if msg:
                                self.messages.append(msg)

                        try:
                            data = self.connection.recv(1024)
                        except ConnectionResetError:
                            data = False

    def get_message(self):
        try:
            r = self.messages[0]
            self.messages = self.messages[1:]  # - 'pop' the processed message off the buffer
            return r
        except IndexError:
            return None

    def send(self, msg):
        """
        Sends bytes
        :param msg: byte string
        """
        if self.connection:
            self.connection.sendall(msg)


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)
    print("Listening for SWP08 messages...")

    server_address = '127.0.0.1'  # - localhost, to exchange data with apps running on the same PC
    port = SWP_PORT

    connection = SwpServer(server_address, port)

    while True:
        received = connection.get_message()
        if received:
            # - If its in the receive buffer then its already been validated by checksum so let's ACK
            print("Validated message received, sending ACK")
            connection.send(bytes(swp_utils.ACK))  # - TODO provide a better way of creating an ACK message, or just change send to accept bytes

            # - TODO - Should not need try/except here, should handle unknown message types better
            # - INFACT has just caused me a headache function call deep within swputils was failing silently!

            valid_message = Message.decode(received)

            if valid_message:
                print("Parsed received from controller: ", received)

                if valid_message.command == "connect":
                    # TODO, should provide the proper connected message not just echoing back...
                    print("...Received message:", valid_message)
                    print("Sending response.")
                    connection.send(Message.connect(valid_message.source, valid_message.destination,
                                                    matrix=valid_message.matrix, level=valid_message.level).encoded)

                elif valid_message.command in ("push_labels", "push_labels_extended"):
                    print("...Received message:", valid_message)

                else:
                    print("Received message type not currently supported")

            else:
                print("Failed to decode received message: ", received)