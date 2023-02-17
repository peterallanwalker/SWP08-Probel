# - Client-side IP socket connection manager for SWP08/Probel controller
# - Buffers incoming messages, provides send and receive methods.
# - Peter Walker, June 2021.

import datetime
import sys
import socket
import threading

import cli_utils
import swp_utils
from swp_unpack import unpack_data as swp

# - V02 - add timestamps to messaging
# - and a log, though that should maybe be in the router
# - router holds msg objects, connection currently only the byte strings, could just convert them again when accessing
# - from the log vs storing msg objects... connection should call back to the router with a confirmed timestamp,
# - have the router then log it, in a separate class.

# - TODO - fix connection retry / reconnect (think it woks for CSCP but isn't for SWP)


TITLE = "Client-side Connection"
VERSION = 1.1
TIMEOUT = 3  # - How long to wait when starting connection and receiving data.
RECEIVE_TIMEOUT = 10


class Connection:
    def __init__(self, ip_address, port=swp_utils.PORT, log=None):
        self.address = ip_address
        self.port = port
        self.sock = None
        self.status = 'Starting'

        # Received message buffer
        self._messages = []
        self._residual_data = False
        # Residual data is received data that cannot be parsed but might be the beginning of a message
        # whose remainder is in the next chunk of data to be received

        # - I'm logging sent messages here in the connection to timestamp them at point of send
        # - but I'm not logging the received messages here... received get timestamped and put into a buffer
        # - ... I'm logging them in the router when popping off the receive buffer
        # - ... to keep receive buffer thread as fast as possible (by not converting to message objects in that thread.
        # - ...    - maybe unnecessary and would be easier to follow if sent and received logging was done in the same
        #            place
        self.log = log
        self.log.log("c", "c", "c")
        self.receiver = threading.Thread(target=self._run)

        # TODO, check the following...
        # Think setting as daemon not necessary but
        # causes thread to stop if main program stops, I.E. control+C to release the terminal
        self.receiver.daemon = True

        self.receiver.start()

    def __str__(self):
        return "Connection object - IP address: {}, port: {}, protocol: {}, status: {}".format(self.address, self.port,
                                                                                               self._protocol,
                                                                                               self.status)

    def _connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(TIMEOUT)
            # self.sock.connect((self.address, self.port))
            #self.sock.connect((self.address, swp_utils.PORT))
            self.sock.connect((self.address, self.port))
            print('[Connection]: Connection established with address {} on port {}'.format(self.address, swp_utils.PORT))

            # I just have to send any message, not this one specifically)
            # TODO - ping device / request some data
            self.status = "Connected"

        except socket.timeout:
            print('[Connection]: socket timeout - Failed to create connection with address {} on port {}'.format(
                self.address, self.port))
            self.close()
            # self.sock = False
            self.sock = None

        except ConnectionRefusedError as e:
            print('[Connection]: socket timeout - Failed to create connection with address {} on port {}'.format(
                self.address, self.port))
            print(e)
            self.close()
            # self.sock = False
            self.sock = None
            sys.exit()

    def _run(self):

        # if not connected, try to create a socket connection.
        while not self.sock:
            if not self.status == 'Connection Lost!':
                self.status = 'Not Connected'
            print("[Connection]: Attempting to connect...")
            self._connect()

        # TODO - test this - if sock.recv timesout does that kill sock, will I still be able to get messages recieved in interim before next call to recv?
        # - this might be causing messages to be missed, faders seem a bit jittery since doing this.

        self.sock.settimeout(RECEIVE_TIMEOUT)
        loop = 0
        self.pinged = False
        while True:
            try:
                data = self.sock.recv(1024)
                # TODO - experiment setting value very small to see if I can split messages and test unpack's residual data on a real connection
            except:
                data = False

            # print('CSCP_connection run: data received', data, 'pinged', self.pinged)

            if data:
                self.pinged = False
                messages, self._residual_data = swp(data, self._residual_data)  # TODO - TEST SPLIT MESSAGES

                if messages:
                    for msg in messages:
                        timestamp = datetime.datetime.now()
                        self._messages.append((timestamp, msg))

            elif self.pinged:
                self.status = "Connection Lost!"
                self.close()
                self._connect()
                self._run()

    # TODO - dont think I'm using this, check proper behaviour for handling sockets and threads
    def close(self):
        self.sock.close
        try:
            self.receiver.stop()
        except:
            pass

    # - PUBLIC METHODS
    def send(self, message):
        #print("[connection.send]: sending", message.summary)
        # - Check if the passed message is raw message bytes or Message object
        if type(message) != bytes:
            message_bytes = message.encoded
        else:
            message_bytes = message
        try:
            self.sock.sendall(message_bytes)
            # TODO - wait 1s for ACK/NAK & retry 3 times before returning?
            #  (if protocol = swp, will break CSCP doing that... test higher up in connectIO)
            if self.log:
                #self.log.log(time.time(), message, 'sent')
                self.log.log(datetime.datetime.now(), message, 'sent')
            return True
        except socket.error as e:
            print("[Connection.send]: Failed to send, error:", e)
            # TODO - check this, not sure this exception will always be a lost connection
            # ... and should detect lost connection before having to send a message
            self.status = "Connection Lost!"
            return False

    def get_message(self):
        if len(self._messages):
            timestamp, oldest_message = self._messages[0]
            self._messages = self._messages[1:]
            #self._received_log.append((timestamp, oldest_message))
            return timestamp, oldest_message
        else:
            return None

    def flush_receive_buffer(self):
        """
        Clears/deletes all messages in the receive buffer
        """
        self._messages = []

    def receive_buffer_len(self):
        """
        :return: int - number of messages in the receive buffer
        """
        return len(self._messages)


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)
    import time

    # address = "172.29.1.24"  # Impulse default SWP08 Router Management adaptor
    # address = "192.169.1.201"  # Impulse added address for SWP08 Router on Interface 3
    address = "127.0.0.1"
    # port = 61000  # Fixed port for SWP08

    # Open a TCP connection with the mixer/router
    connection = Connection(address)

    time.sleep(1)
    print("[{}] :".format(TITLE), connection)

    while True:
        message = connection.get_message()
        if message:
            print("[{}]: messages in receive buffer: {}, message: {}".format(TITLE, len(connection._messages),
                                                                                        message))
