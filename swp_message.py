# - SWP08/Probel Message classes
# - Peter Walker, May 2022
# -
# - SWP08 Protocol doc:
# - https://github.com/peterallanwalker/SWP08-Probel/blob/master/protocol%20docs/SW-P-08%20Issue%2032.pdf

import cli_utils
import swp_utils as utils
from swp_node import Node
import swp_node

TITLE = 'SWP Messages'
VERSION = 0.3


def _format_message(payload):
    """
    Takes swp command payload as list of ints per byte, adds byte-count & checksum, escapes any DLE values,
    then wraps with SOM & EOM and returns as byte-string ready to be sent over a socket.
    :param payload: list - ints representing command bytes.
    :return: byte string - encoded SWP message.
    """
    payload = list(payload)
    byte_count = len(payload)
    payload.append(byte_count)
    checksum = utils.calculate_checksum(payload)
    payload.append(checksum)

    payload = bytes(payload)
    if utils.DLE in payload:
        # - Escape any DLE values within the payload
        payload.replace(bytes([utils.DLE]), bytes([utils.DLE, utils.DLE]))

    message = bytes(utils.SOM) + payload + bytes(utils.EOM)
    return message


def decode(encoded_message):
    """
    :param encoded_message: bytes, pre-validated SWP message as sent/received by a socket
    :return: Message object of the appropriate Class
    """
    # First check if bytes are a simple ACK or NAK message
    if encoded_message == bytes(utils.ACK):
        return Response()
    elif encoded_message == bytes(utils.NAK):
        return Response(response='NAK')
    else:
        # Get the value of the command byte and lookup the key for that value in utils.COMMANDS
        try:
            command = list(utils.COMMANDS.keys())[
                list(utils.COMMANDS.values()).index(encoded_message[utils.COMMAND_BYTE])]
        except ValueError:
            print(f'[swp_message.decode]: Command not supported: {encoded_message[utils.COMMAND_BYTE]}')
            return None

        # Create an swp_message object based on the command type
        if command in ('connect', 'connected'):
            source, destination = utils.decode_connect_source_destination(encoded_message)
            matrix, level = utils.decode_matrix_level(encoded_message)
            return Connect(source, destination, matrix, level, command)

        elif command in ('push_labels', 'push_labels_extended'):
            destination = utils.decode_labels_destination(encoded_message)
            matrix, level = utils.decode_matrix_level(encoded_message)
            labels = utils.get_labels(encoded_message)
            # - get the value of the character length byte and look up its key to get the actual char length
            char_len = list(utils.CHAR_LEN_CODES.keys())[
                list(utils.CHAR_LEN_CODES.values()).index(encoded_message[utils.CHAR_LEN_BYTE])]
            return PushLabels(destination, labels, matrix, char_len)

        elif command == 'cross-point tally dump request':
            matrix, level = utils.decode_matrix_level(encoded_message)
            return GetConnections(matrix, level)

        # TODO, handle "cross-point tally dump (byte)" message type
        # elif command in ("cross-point tally dump (byte)", "cross-point tally dump (word/extended)"):
        elif command == "cross-point tally dump (word/extended)":
            # - TODO I'm getting matrix & level in the same way for every message type so far, so move to above
            matrix, level = utils.decode_matrix_level(encoded_message)
            tallies = encoded_message[utils.COMMAND_BYTE + 2]  # Number of connections represented in the message

            first_destination_div = encoded_message[utils.COMMAND_BYTE + 3]
            first_destination_mod = encoded_message[utils.COMMAND_BYTE + 4]
            first_destination = 256 * first_destination_div + first_destination_mod
            destinations = []
            connected_sources = []

            for i in range(tallies):
                # decode the source ID and create a source node object
                div = encoded_message[utils.COMMAND_BYTE + 5 + (i * 2)]
                mod = encoded_message[utils.COMMAND_BYTE + 6 + (i * 2)]
                source_id = 256 * div + mod
                connected_sources.append(Node.source(matrix, level, source_id))

                # create destination node object (only the first destination is available in the encoded message,
                # The subsequent ones have consecutive IDs
                destination = Node.destination(matrix, level, first_destination + i)
                destination.connected_source = connected_sources[i]
                destinations.append(destination)

            return CrossPointTallyDumpWord(destinations)

        else:
            # raise ValueError(f"[swp_massage.decode]: {command} command not yet supported")
            print(f"[swp_massage.decode]: {command} command not yet supported")
            return None


class Response:
    def __init__(self, response="ACK"):
        self.command = response
        if response == "ACK":
            self.encoded = bytes(utils.ACK)
        elif response == "NAK":
            self.encoded = bytes(utils.ACK)
        else:
            raise ValueError("[swp_message.Response]: response must be 'ACK' or 'NAK'")

    def __str__(self):
        if self.command == 'ACK':
            description = " - Receipt of valid message acknowledged"
        else:
            description = " - Not Acknowledged (Router received our message but not as valid SWP encoding)"
        return "[swp_message object]: Command: {}{}".format(self.command.upper(), description)


class Connect:
    """
    Cross Point Connect message - SWP protocol Command 2 (protocol doc 3.1.3, page 13), issued by controllers.
    Or pass command="connected" to the constructor for a Cross Point Connected - message 4 (protocol doc 3.2.3, page 33)
    as issued by a router.
    On sending a Connect message, a router should respond with an ACK followed by a Connected message if it has the
    relevant source and destination and connects them.
    """

    def __init__(self, source, destination, matrix=None, level=None, command="connect"):
        """
        :param source: Either Node or int
        :param destination: Either Node or int
        :param matrix: int if int passed for source & destination
        :param level: int if int passed for source & destination
        :param command:
        """

        if type(source) is Node and type(destination) is Node:
            if utils.is_same_matrix_and_level(source, destination):
                self.source = source.id
                self.destination = destination.id
                self.matrix = source.matrix
                self.level = source.level
            else:
                error_message = "[swp_message.Connect]:Invalid arguments. Can only connect source with destination " \
                                "on same matrix and level. \n\t{}\n\t{}".format(source, destination)
                raise ValueError(error_message)

        elif type(source) is int and type(destination) is int and type(matrix) is int and type(level) is int:
            self.source = source
            self.destination = destination
            self.matrix = matrix
            self.level = level

        else:
            error_message = "[swp_message.Connect]:Invalid arguments - source: {}, destination: {}, " \
                            "matrix: {}, level: {}".format(source, destination, matrix, level)
            raise ValueError(error_message)

        self.command = command
        self.encoded = self._encode()

    def _encode(self):
        matrix_level = utils.encode_matrix_level(self.matrix, self.level)
        multiplier = utils.encode_source_destination_multiplier(self.source, self.destination)
        data = utils.COMMANDS[self.command], matrix_level, multiplier, self.destination % 128, self.source % 128
        return _format_message(data)

    def __str__(self):
        return "[swp_message object]: Command: {} ({}), matrix: {}, level: {}, " \
               "source: {}, destination: {}".format(self.command.upper(), utils.COMMANDS[self.command],
                                                    self.matrix, self.level, self.source, self.destination, )


class Connected(Connect):
    def __init__(self, source, destination, matrix=None, level=None):
        if type(source) is Node and type(destination) is Node:
            super().__init__(source, destination, command='connected')

        elif type(source) is int and type(destination) is int and type(matrix) is int and type(level) is int:
            super().__init__(source, destination, matrix=matrix, level=level, command='connected')


class GetConnections:
    """
    Cross-point tally dump request - SWP protocol command 21 (protocol doc 3.1.11, page 18)
    issued by controllers to get current connection state of a router for a given matrix and level.
    The router will respond with Cross-point tally dump byte or word message - SWP protocol Command 22 or 23
    (protocol doc 3.2.10, page 36 or 3.2.11, page 37)
    """

    def __init__(self, matrix, level):
        """
        :param matrix: int
        :param level: int
        """
        self.command = "cross-point tally dump request"
        self.matrix = matrix
        self.level = level
        self.encoded = self._encode()

    def _encode(self):
        matrix_level = utils.encode_matrix_level(self.matrix, self.level)
        data = utils.COMMANDS[self.command], matrix_level
        return _format_message(data)

    def __str__(self):
        return "[swp_message object]: Command: {} ({}), matrix: {}, level: {}" \
            .format(self.command.upper(), utils.COMMANDS[self.command], self.matrix, self.level)


class CrossPointTallyDumpWord:
    def __init__(self, destinations):
        """
        :param destinations: list of up to 64 consecutive ID'd destination Nodes
        (provided by swp_node.get_consecutive_nodes())
        """
        if len(destinations) > 64:
            print(f'[{TITLE}.CrossPointTallyDumpWord]: Max number of tallies per message is 64,'
                  f' {len(destinations)} received')
        else:
            self.command = "cross-point tally dump (word/extended)"
            # This message type only passes the first destination's ID, the number of tallies/connections in the message
            # and source IDs for the given destination and every following consecutive ID'd destination,
            # up to a max of 64. It assumes all destinations and sources are of the same matrix & level.
            self.first_destination = destinations[0]
            self.matrix = self.first_destination.matrix
            self.level = self.first_destination.level
            self.sources = swp_node.get_connected_sources(destinations)
            self.verbose = self._verbose_listing()
            self.encoded = self._encode()

    def _encode(self):
        matrix_level = utils.encode_matrix_level(self.matrix, self.level)
        data = [utils.COMMANDS[self.command], matrix_level, len(self.sources)]
        data += utils.div_mod(self.first_destination.id)
        for source in self.sources:
            source = utils.div_mod(source)
            data += source
        return _format_message(data)

    def _verbose_listing(self):
        r = ''
        for i, src in enumerate(self.sources):
            r += f'Destination {self.first_destination.id + i} <- Source {src}\n'
        return r

    def __str__(self):
        return f'[swp_message object]: command:{self.command}, matrix:{self.matrix}, level:{self.level}, ' \
               f'\nConnections:\n{self.verbose}'


class PushLabels:
    """
    Destination Association Names Response Message - SWP protocol command 107 (protocol doc 3.2.20, page 46).
    Labels get displayed in Calrec fader and meter displays where the destinations are patched to them.
    If multiple labels passed they are associated with consecutive destinations.
    Calrec routers accept this message being sent unsolicited and respond with an ACK.
    Calrec will automatically update the labels of any other destinations that are connected from the same source
    as any destinations that are explicitly getting labels pushed to them.
    """
    def __init__(self, first_destination, labels, matrix=0, char_len=12):
        """
        :param first_destination: Node object or int representing ID of the destination for the first label
        :param labels: list of strings - one per destination label
        :param char_len: int - Length to truncate the labels to; 4, 8, 12, 16, 32 character length labels
                         are supported by the protocol. Calrec has a max len of 12 and will truncate to 12
                         if passed 16 or 32 char length labels.
        """
        if type(first_destination) is Node:
            # - Note, this message type is only supported for level 0
            # - ... I assume the intention is that levels are used to split channels of the same path
            # - using the same matrix and ID (I should provide an option to "link levels" when making connections.
            # - e.g. if "main 1 L" is matrix a, level 0, id b, then "main 1 R should be matrix a level 1, id b
            if first_destination.level != 0:
                raise ValueError("[swp_message.PushLabels]: Labels can only be pushed to level 0, level {} was passed"
                                 .format(self.destination.level))
            self.destination = first_destination.id
            self.matrix = first_destination.matrix
            self.level = 0

        elif type(first_destination) is int and type(matrix) is int:
            self.destination = first_destination
            self.matrix = matrix
            self.level = 0

        else:
            error_message = "[swp_message.PushLabels]:Invalid arguments - destination: {}, " \
                            "matrix: {}".format(first_destination, matrix)
            raise ValueError(error_message)

        self.command = "push_labels"
        self.char_len = char_len
        self.labels = utils.set_label_length(labels, self.char_len)
        self.encoded = self._encode()

    def _encode(self):
        labels = utils.format_labels(self.labels)
        matrix_level = utils.encode_matrix_level(self.matrix, self.level)
        data = [utils.COMMANDS[self.command], matrix_level, utils.CHAR_LEN_CODES[self.char_len],
                int(self.destination / 256), self.destination % 256, len(self.labels)] + labels
        return _format_message(data)

    def __str__(self):
        return "[swp_message_object]: Command: {} ({}), matrix: {}, level: {}, first destination: {}, label/s: {}" \
            .format(self.command.upper(), utils.COMMANDS[self.command],
                    self.matrix, self.level, self.destination, self.labels)


# TEST FUNCTIONS

def test_connect():
    # - Proven connect message for matrix 0, level 0, source 0, destination 1
    test_results = [b'\x10\x02\x02\x00\x00\x01\x00\x05\xf8\x10\x03',
                    # - Proven connect message for matrix 2, level 3, source 100, destination 200
                    b'\x10\x02\x02#\x10Hd\x05\x1a\x10\x03',
                    # - Proven connect message for matrix 2, Level 3, source: 300, destination: 999,
                    b'\x10\x02\x02#rg,\x05\xd1\x10\x03']

    test_messages = [Connect(0, 1, 0, 0),
                     Connect(Node.source(2, 3, 100), Node.destination(2, 3, 200)),
                     Connect(Node.source(2, 3, 300), Node.destination(2, 3, 999))]

    for i, test in enumerate(test_messages):
        # print("message:", test, type(test.encoded))
        # print("sample:", test_results[i], type(test_results[i]))
        if test.encoded == test_results[i]:
            print("Test Connect {}: PASS".format(i + 1))
        else:
            print("Test Connect {}: FAIL".format(i + 1))


def test_connected():
    # - Sample Connected message received from a router
    # - for source 10 to dest 0 on matrix 0 level 0
    test_result = b'\x10\x02\x04\x00\x00\x00\n\x05\xed\x10\x03'

    src_id = 10
    dest_id = 0
    src = Node.source(0, 0, src_id)
    dst = Node.destination(0, 0, dest_id)

    messages = [Connect(src, dst, command="connected"),
                Connected(src_id, dest_id, matrix=0, level=0),
                Connected(src, dst)]

    for i, msg in enumerate(messages):
        # print("message:", msg, type(msg.encoded))
        # print("sample:", test_result, type(test_result))
        if msg.encoded == test_result:
            print("Test Connected {}: PASS".format(i + 1))
        else:
            print("Test Connected {}: FAIL".format(i + 1))


def test_push_labels():
    dest = Node.destination(0, 0, 0)
    test_labels = [["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"],
                   ["testing", "eight", "char", "labels", "so", "some very long"]]

    test_results = [
        b'\x10\x02k\x00\x02\x00\x00\none         two         three       four        five        six         ' \
        b'seven       eight       nine        ten         ~Z\x10\x03',
        b'\x10\x02k\x00\x01\x00\x00\x06testing eight   char    labels  so      some ver65\x10\x03']

    test_messages = [PushLabels(0, test_labels[0], matrix=0),
                     PushLabels(dest, test_labels[1], char_len=8)]

    for i, message in enumerate(test_messages):
        # print("message:", message.encoded, type(message.encoded))
        # print("sample:", test_results[i], type(test_results[i]))
        if message.encoded == test_results[i]:
            print("Test Push Labels {}: PASS".format(i + 1))
        else:
            print("Test Push Labels {}: FAIL".format(i + 1))


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)
    print("Tests...")
    test_connect()
    test_connected()
    test_push_labels()

