# - Server-side IP socket connection manager for SWP08/Probel Router (used by router emulator)
# - Buffers incoming messages, provides send and receive methods.
# - Peter Walker, June 2022.
# - Ref for working with sockets: https://realpython.com/python-sockets/

import socket
import threading
import datetime

import cli_utils
import swp_utils
from swp_unpack import unpack_data

TITLE = "Socket Connection Manager"
VERSION = 0.1
LOCALHOST = "127.0.0.1"
CLIENT_CONNECTION_TIMEOUT = 3

# TODO - Check is a router responds with an ACk if sent an ACK
#        or find a benign message type that change be sent to check if the client connection is
#        still up to client _run can check and restart


class Connection:
    def __init__(self, ip_address, log=None):
        self.connection = None  # - the socket connection
        self.status = False
        self.address = ip_address
        self.log = log
        self.messages = []  # - Buffer for storing received messages

        # - For storing data from end of a received chunk if it looks like the beginning of another message,
        # - to check for the rest of it in the next chunk
        self.residual_data = None

    def _buffer_incoming_messages(self):
        data = self.connection.recv(1024)  # - Receive up to 1MB of data
        while data:
            msgs, residual_data = unpack_data(data)
            for msg in msgs:
                self.messages.append((datetime.datetime.now(), msg))

            try:
                data = self.connection.recv(1024)
            except ConnectionResetError:
                data = False

    ########################
    # -- PUBLIC METHODS -- #
    def get_received_message(self):
        """
        Returns and removes the first/oldest message in the received message buffer.
        :return: tuple - (datetime.datetime object, swp_message object) or (None, None)
        """
        if self.messages:
            return self.messages.pop(0)
        return None, None

    def send_message(self, message):
        """
        :param message: bytes or swp_message object
        """
        if type(message) != bytes:
            message = message.encoded

        if self.connection:
            try:
                self.connection.sendall(message)
            except OSError:
                print(f'[{TITLE}.Connection.send_message]: Failed to send message')

    def flush_receive_buffer(self):
        self.messages = []


class Server(Connection):
    """ Server-side, for SWP router emulator """
    def __init__(self, ip_address, log=None):
        super().__init__(ip_address, log)
        # - Set up to receive messages in a separate thread
        self.receiver = threading.Thread(target=self._run)
        self.receiver.daemon = True  # - Can't remember, think I need this to be able to quit.stop thread with control+c
        self.receiver.start()  # - Starts the thread, calling the target (_run())

    def _run(self):
        """ Called by self.receiver.start on initialisation """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.address, swp_utils.PORT))
            while True:
                s.listen()

                # - s.accept() seems to block until a client connects in
                self.connection, addr = s.accept()
                self.status = True
                with self.connection:
                    print(f'[{TITLE}.Server]: New connection with client:', addr, self.connection)
                    self._buffer_incoming_messages()


class Client(Connection):
    """ Client-side, for SWP controller """
    def __init__(self, ip_address, log=None):
        super().__init__(ip_address, log)
        # - Set up to receive messages in a separate thread
        self.receiver = threading.Thread(target=self._run)
        self.receiver.daemon = True  # - Can't remember, think I need this to be able to quit.stop thread with control+c
        self.receiver.start()  # - Starts the thread, calling the target (_run())

    def _run(self):
        """ Called by self.receiver.start on initialisation """
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.settimeout(CLIENT_CONNECTION_TIMEOUT)

        while not self.status:
            try:
                self.connection.connect((self.address, swp_utils.PORT))
                self.status = True
                # send an ACK to check if up, handle exceptions and reconnect if fails.
                print('[{}.Client]: Connection established with server on address {} port {}'.format(TITLE,
                                                                                                     self.address,
                                                                                                     swp_utils.PORT))
            except ConnectionRefusedError:
                print(f'[{TITLE}.Client._run]: Connection Refused')

        with self.connection:
            self._buffer_incoming_messages()


if __name__ == '__main__':
    import swp_message_03 as swp
    import time
    cli_utils.print_header(TITLE, VERSION)
    server = Server(LOCALHOST)
    print("Server running and listening for client connection...")

    ack = swp.Response()
    while True:
        timestamp, received = server.get_received_message()
        if received:
            print(timestamp, received)
            server.send_message(bytes(swp_utils.ACK))
            server.send_message(ack)

        server.send_message(swp.Response(response="NAK"))
        time.sleep(1)