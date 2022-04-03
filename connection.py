# CONNECTION
# IP connection manager, buffers incoming messages, provides send and receive methods
# Peter Walker, June 2021
# Based on CSCP_connection, let's aim to keep it generic, with SWP08 specific handling external to this file.

import socket
import threading

#import swp_unpack as swp
# TODO - unpack 2 has not been tested with Connection
import swp_unpack_02 as swp

# import CSCP_unpack_1_1 as cscp

TIMEOUT = 3  # how long to wait when starting connection and receiving data.
RECEIVE_TIMEOUT = 10


class Connection:

    def __init__(self, address, port, protocol="CSCP"):

        self._protocol = protocol

        # Set the function to use for unpacking data based on the protocol being used
        if protocol == "CSCP":
            self._unpack = cscp.unpack_data
        elif protocol == "SWP08":
            self._unpack = swp.unpack_data

        self.address = address
        self.port = port

        # self.sock = False
        self.sock = None
        self.status = 'Starting'

        self._messages = []
        self._residual_data = False  # Residual data that cannot be parsed but might be the beginning of a message
        # whose remainder is in the next data to be received

        # self.connect()
        self.receiver = threading.Thread(target=self.run)
        self.receiver.daemon = True  # trying this, should cause thread to stop if main program stops, I.E. control+C to release the terminal
        self.receiver.start()

    def __str__(self):
        return "Connection object - IP address: {}, port: {}, protocol: {}, status: {}".format(self.address, self.port,
                                                                                               self._protocol,
                                                                                               self.status)

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(TIMEOUT)
            self.sock.connect((self.address, self.port))
            print('[Connection]: Connection established with address {} on port {}'.format(self.address, self.port))

            # I just have to send any message, not this one specifically)
            # TODO - ping device / request some data
            self.status = "Connected"

        except socket.timeout:
            print('[Connection]: socket timeout - Failed to create connection with address {} on port {}'.format(
                self.address, self.port))
            self.close()
            # self.sock = False
            self.sock = None

    def run(self):

        # if not connected, try to create a socket connection.
        while not self.sock:
            if not self.status == 'Connection Lost!':
                self.status = 'Not Connected'
            print("[Connection]: {}. Attempting to connect...".format(self.status))
            self.connect()

        # TODO - test this - if sock.recv timesout does that kill sock, will I still be able to get messages recieved in interim before next call to recv?
        # - this might be causing messages to be missed, faders seem a bit jittery since doing this.

        self.sock.settimeout(RECEIVE_TIMEOUT)
        loop = 0
        self.pinged = False
        while True:
            try:
                data = self.sock.recv(1024)
                # TODO - experiment setting value very small to see if I can split messages and test unpack's residual data
            except:
                data = False

            # print('CSCP_connection run: data received', data, 'pinged', self.pinged)

            if data:
                self.pinged = False
                print("[connection.py.run]: DATA RECEIVED", data)

                messages, self._residual_data = self._unpack(data, self._residual_data)  # TODO - TEST SPLIT MESSAGES

                if messages:
                    for msg in messages:
                        self._messages.append(msg)

            elif self.pinged:
                self.status = "Connection Lost!"
                self.close()
                self.connect()
                self.run()

    def send(self, message):
        try:
            self.sock.sendall(message)
        except self.sock.error as e:
            print("[Connection.send]: Failed to send, error:", e)
            return False
        # TODO - wait for ACK/NAK before returning? (if protocol = swp, will break CSCP doing that... test higher up in connectIO)

    # TODO - dont think I'm using this?
    def receive(self):
        """ Check Receive Buffer """
        self.sock.settimeout(None)
        data = self.sock.recv(1024)
        return data

    # TODO - dont think I'm using this, check proper behaviour for handling sockets and threads
    def close(self):
        self.sock.close
        try:
            self.receiver.stop()
        except:
            pass

    def get_message(self):
        if len(self._messages):
            oldest_message = self._messages[0]
            self._messages = self._messages[1:]
            return oldest_message
        else:
            return None

    def flush_receive_buffer(self):
        self._messages = []


if __name__ == '__main__':

    import time

    print(20 * '#' + ' IP Connection Manager' + 20 * '#')

    # address = "172.29.1.24"  # Impulse default SWP08 Router Management adaptor
    address = "192.169.1.201"  # Impulse added address for SWP08 Router on Interface 3

    port = 61000  # Fixed port for SWP08

    # Open a TCP connection with the mixer/router
    connection = Connection(address, port, protocol="SWP08")

    # print("[connection.py] :", connection)
    time.sleep(1)
    print("[connection.py] :", connection)

    while True:
        message = connection.get_message()
        if message:
            print("[connection_01]: messages in receive buffer: {}, message: {}".format(len(connection._messages),
                                                                                        message))
