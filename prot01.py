
# Attempting SWP08 control
# let's start with building a connection

# SWP08 protocol info:
# https://wwwapps.grassvalley.com/docs/Manuals/sam/Protocols%20and%20MIBs/Router%20Control%20Protocols%20SW-P-88%20Issue%204b.pdf

import socket
import threading
import time

TIMEOUT = 3  # how long to wait when starting connection and receiving data.
RECEIVE_TIMEOUT = 10

COMMANDS = {"connect": 0x04,    # TODO - DEBUG - set to 4 to check, should be 2! Send to router to set a connection
            "connected": 0x04,  # Sent from router when a connection is made
            }


def calculate_checksum(data):
    """
        Calculate checksum for an SWP08 message
        :param data: an array/list of values,
            one per byte of an SWP08 message's DATA and BTC (byte count)
    """
    checksum = 0
    for value in data:
        checksum += value

    checksum = twoscomp(bin(checksum))

    return checksum


class Connection:

    def __init__(self, address, port):

        self.address = address
        self.port = port
        self.sock = False
        self.status = 'Starting'

        self.messages = []
        self.residual_data = False  # Residual data that cannot be parsed but might be the beginning of a message
                                    # whose remainder is in the next data to be received

        #self.connect()
        self.receiver = threading.Thread(target=self.run)
        self.receiver.daemon = True # trying this, should cause thread to stop if main program stops, I.E. control+C to release the terminal
        self.receiver.start()

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(TIMEOUT)
            self.sock.connect((self.address, self.port))
            print('SWP08_connection: Socket connection established with address {} on port {}'.format(self.address, self.port))

                                                          # I just have to send any message, not this one specifically)
            self.status = "Connected"

        except:
            print('SWP08_connection: Failed to create connection')
            self.close()
            self.sock = False

    def run(self):

        # if not connected, try to create a socket connection every 5s.
        while not self.sock:
            if not self.status == 'Connection Lost!':
                self.status = 'Not Connected'
            self.connect()
            #time.sleep(5)



        # TODO - test this - if sock.recv timesout does that kill sock, will I still be able to get messages recieved in interim before next call to recv?
        self.sock.settimeout(RECEIVE_TIMEOUT)  # - this might be causing messages to be missed, faders seem a bit jittery since doing this.
        loop = 0
        self.pinged = False
        while True:
            try:
                data = self.sock.recv(1024)  # TODO - experiment setting value very small to see if I can split messages and test unpack's residual data
            except:
                data = False

            #print('CSCP_connection run: data received', data, 'pinged', self.pinged)

            if data:
                self.pinged = False
                print(data)
                self.messages.append(data)  # TODO - parse before storing, and create a get method.
                
            elif self.pinged:
                self.status = "Connection Lost!"
                self.close()
                self.connect()
                self.run()

            

    def send(self, message):
        try:
            self.sock.sendall(message)
        except:
            pass

    def receive(self):
        """ Check Receive Buffer """
        self.sock.settimeout(None)
        data = self.sock.recv(1024)
        return data

    def close(self):
        self.sock.close
        try:
            self.receiver.stop()
        except:
            pass


class Message:

    SOM = [0x10, 0x02]  # SWP08 Message header ("Start Of Message")
    EOM = [0x10, 0x03]  # SWP08 Message end ("End of Message")

    def __init__(self,
                 command=None,
                 matrix=None,
                 level=None,
                 multiplier=None,
                 source=None,
                 destination=None,
                 encoded=None,):
        """
            *** NOT INTENDED TO BE CALLED DIRECTLY, INSTANTIATE USING THE CLASS METHODS...
            - e.g call Message.connect(source, destination) to instantiate a connect message using source/dest values
            - or call Message.decode(msg byte string) to instantiate a message object from its encoded form.
        """
        if encoded:
            # TODO -decode
            pass

        else:
            self._command = command

            if not matrix:
                self._matrix = 0
            if not level:
                self._level = 0
            if not multiplier:
                self._multiplier = 0

            self._source = source
            self._destination = destination

            self._encoded = self._encode()

    def __str__(self):
        return "SWP08 Message object - Command: {}, Matrix: {}, Level: {}, Multiplier: {}, Source: {}, Destination: {}\
                , Encoded: {}".format(self._command, self._matrix, self._level, self._multiplier, self._source,
                                      self._destination, self._encoded)

    """ PUBLIC CONSTRUCTORS FOR INSTANTIATING THIS CLASS """
    @classmethod
    def connect(cls, source, destination, matrix=0, level=0, multiplier=0):
        """
        Instantiate a connection Message object
        :param source:
        :param destination:
        :param matrix:
        :param level:
        :param multiplier:
        :return:
        """
        message = Message(command="connect", source=source, destination=destination, matrix=matrix, level=level,
                          multiplier=multiplier)
        return message

    @classmethod
    def decode(cls, message):
        """
        Instantiate a Message object using an encoded byte string
        :param message:
        :return:
        """
        message = Message(encoded=message)
        return message

    def _encode(self):
        """
            Encodes message params into SWP08 protocol byte string
            SWP08 message format - SOM, DATA, BTC, CHK, EOM
            :return: SWP08 encoded byte string, ready to send to mixer
        """

        data = [COMMANDS[self._command]] + [self._matrix, self._multiplier, self._destination, self._source]
        byte_count = len(data)
        print("DEBUG byte count:", byte_count)
        data.append(byte_count)
        checksum = calculate_checksum(data)

        message = Message.SOM + data + [int(checksum, 16),] + Message.EOM
        print("DEBUG message", message)
        return bytes(message)


def twoscomp(value):
    # take a binary string, returns twos compliment... there must be a better way of doing this!
    # TODO - THIS WILL BREAK IF PASSED NUMBER > 8 bits
    # TODO update: previously when this returned > 0xFF I found setting it to 0x00 fixed but was confused why
    # TODO update... think possibly I should just pass the last 8 bits???? - that's what I'm now doing instead and seems to work

    #print('DEBUG, CSCP_utils, twoscomp received:', value, len(value))
    result = ''

    missing = 10 - len(value)  # check supplied value is 8 bits (accounting for it being a string, prefixed with "0b"
    result = missing * "1"  # pad out missing 8 bit MSB 0's with 1's (inverting as part of 2's comp)

    for bit in range(2, len(value)):  # get rid of the "0b" at the beginning of the binary string and loop through bits
        # invert bits
        if value[bit] == "1":
            result += "0"
        elif value[bit] == "0":
            result += "1"

    #print('DEBUG, CSCP_utils, twoscomp inverted:', result, len(result))

    # add one to the result
    result = int(result, 2) + 1 # TODO, should be able to +1 without converting to int

    # New hack - instead of just setting returned hex to 0x0 if > 0xFF, which seemed to work, but would prosssibly
    # fail if higher values encountered convert to hex (again, there must be a better way of doing this!!!)
    if result > 255:
        result = bin(result)

        #print('DEBUG, CSCP_utils, twoscomp +1:', result, len(result))

        result = (result[-8:])

        result = int(result, 2)
    
    print("TWOSCOMP", result)
    return hex(result)


if __name__ == '__main__':

    # Sample message from mixer - Connected
    test_message = b'\x10\x02\x04\x00\x00\n\x00\x05\xed\x10\x03'

    test1 = Message.connect(0, 10)
    #test2 = Message.decode(test_message)

    print("TEST1", test1)
    #print("TEST1", test2)



    #address = "192.169.1.200"  # My mixers configured "External COntrol" port
    #address = "172.29.1.24"     # Impulse default Router Management adapaptor
    address = "192.169.1.201"   # Impulse added address for Router on Interface 3
    
    
    #port = 12345  # CSCP port configured on my mixers
    port = 61000  # Fixed port for SWP08

    print (20*'#'+' SWP08_connection ' + 20*'#')

    connection = Connection(address, port)
    
    
    time.sleep(2)
    print("SENDING TEST SWP08 MESSAGE")
    
    # THis is the messaeg I get from the mixer when I make a patch
    #msg = b'\x10\x02\x04\x00\x00\x14\n\x05\xd9\x10\x03'
    # but sending it to the mixer does not make a patch, but it returns b'x10\x06' - so is a valid message, but just a confirmation
    
    SOM = b'\x10\x02'
    
    #COMMAND = b'\x02'  # Crosspoint connect message
    COMMAND = b'\x04'   # crosspoint connected message (what I get back from the mixer when crosspoints made)
    
    
    MATRIX = b'\x00' # == 1 in Configure
    MULTIPLIER = b'\x00'
    
    DESTINATION = b'\x0a'  # dec 10, set as ID 11 in Configure
    SOURCE = b'\x00'       # 0, set as ID 1 in Configure

    BTC = b'\x05'  # BYTE COUTNT OF THE DATA FIELD # TODO - CALC THIS NOT HARD CODE!
    
    DATA = COMMAND + MATRIX + MULTIPLIER + DESTINATION + SOURCE + BTC
    #data2 = [COMMAND, MATRIX, MULTIPLIER, DESTINATION, SOURCE]

    print("DEBUG, data:")
    for v in DATA:
        print(v)

    checksum = 0
    for v in DATA:
        checksum += v
    print("checksum:", checksum)
    checksum = bin(checksum)


    
    print("DEBUG", DATA + BTC)
    
    #CHECKSUM = twoscomp(DATA + BTC)
    #CHECKSUM = twoscomp([int(DATA), int(BTC)])
    CHECKSUM = twoscomp(checksum)
    
    print("Checksum", CHECKSUM, type(CHECKSUM))
    CHECKSUM = int(CHECKSUM, 16)
    print("Checksum", CHECKSUM, type(CHECKSUM))
    
    CHECKSUM = bytes([CHECKSUM])
    
    print("Checksum", CHECKSUM, type(CHECKSUM))
    
    EOM = b'\x10\x03'
    
    print ("cehcksum", CHECKSUM)
    
    #CHECKSUM = bytes([237]) # hardcode for test case to match what I get from mixer!
    
    msg = SOM + DATA + CHECKSUM + EOM
    
    # This is a recieved message with byte 3 changed from 2 (connected) to 4 (connect)
    #msg = b'\x10\x02\x02\x00\x00\n\x00\x05\xed\x10\x03' 
    # DOES NOT WORK AS CHECKSUM WILL BE WRONG!
    #msg = b'\x10\x02\x04\x00\x00\n\x00\x05\xed\x10\x03' 
    
    
    
    print("SENDING:", msg)
    print ("length", len(msg))
    
    for ch in msg:
        print(ch, end=" - ")
    
    connection.send(msg)
    
    # example received crosspoint message:
    # b'\x10\x02\x04\x00\x00\x14\n\x05\xd9\x10\x03'
    # \x10\x02 - SOM
    # \x04 - COMMAND - "CROSSPOINT CONNECTED"
    # \x00\x00\x14\n
    
    # \x05 - BTC
    # \xd9 - CHECKSUM
    # \x10\x03 - EOM
    
    
    

    i = 0
    while True:

        print('\n', i, 'qty:', len(connection.messages), 'residual data', connection.residual_data)
        
        for message in connection.messages:
            print("message recieved:")
            print(message)
            print ("len", len(message))
            for ch in message:
                print(ch, end=" - ")

        i += 1
        time.sleep(2)


