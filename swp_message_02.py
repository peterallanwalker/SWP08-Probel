# SWP08 Message Class
# For encoding and decoding router control messages using the SWP08/Probel protocol
# Message.encoded is a byte string ready to be sent by Connection.send()
# Peter Walker, June 2021
#
# Updated March 2022 - Added support for pushing labels
# ... Note this is not typical usage of the protocol,
#     it is used by VSM to push labels to Calrec Apollo/Artemis audio mixers

# SWP08 protocol info:
# https://wwwapps.grassvalley.com/docs/Manuals/sam/Protocols%20and%20MIBs/Router%20Control%20Protocols%20SW-P-88%20Issue%204b.pdf
# Other versions of the protocol doc are available in the project's protocol docs folder

import swp_utils as utils
import cli_utils


def is_same_matrix_and_level(source, destination):
    if source.matrix == destination.matrix and source.level == destination.level:
        return True
    else:
        return False


def set_label_len(labels, char_len):
    """
    Check label lengths and truncate if necessary
    :param labels: list of strings
    :param char_len: int - number of chars for label format.
    :return: list of strings
    """
    valid_label_lengths = (4, 8, 12, 16, 32)
    if char_len not in valid_label_lengths:
        print("[swp_message.set_label_len]: Invalid character length: {}, must be one of: {}".format(char_len, valid_label_lengths))
        return False
    else:
        fixed_len = []
        for label in labels:
            if len(label) > char_len:
                # - Truncate long labels
                fixed_len.append(label[:char_len])
            else:
                # - Pad short labels
                fixed_len.append(label.ljust(char_len))

        return fixed_len


def format_labels(labels):
    r = []
    for label in labels:
        for char in label:
            r.append(ord(char))

    return r


class Message:
    """
    *** Message() NOT INTENDED TO BE CALLED DIRECTLY, INSTANTIATE USING THE CLASS METHODS... ***
    - e.g call Message.connect(...) to instantiate a connect message using source/dest values,
    - or call Message.push_labels(...) to instantiate a label message,
    - or call Message.decode(msg byte string) to instantiate a message object from its encoded form.
    """

    def __init__(self,
                 command=None,
                 matrix=None,
                 level=None,
                 source=None,
                 destination=None,
                 char_len=None,
                 labels=None,
                 encoded=None):

        # If public Message.decode constructor used, it is passed the raw byte string of a pre-validated message
        # which gets passed to the init as encoded='<raw message byte string>'
        # ... and the we extract the data to populate the class attributes:
        if encoded:
            # - Encoded messages from Connect.get_message() are pre-validated by header & checksum (by swp_unpack),
            # - so do not need revalidating here.
            self.labels = False  # - TODO - sort having to deal with missing attributes better!
            self.encoded = encoded
            #print("DEBUG MESSAGE DECODE", self.encoded, bytes(utils.ACK))
            # - Check if the encoded message is a simple ACK/NAK and process accordingly
            if self.encoded == bytes(utils.ACK):
                self.command = "ACK"
                # TODO HANDLE THIS BETTER - FIX __str__ for None or fix init to replace None with False
                self.matrix = 0
                self.level = 0
                self.multiplier = 0
                self.source = False
                self.destination = False

            elif self.encoded == bytes(utils.NAK):
                self.command = "NAK"
                # TODO HANDLE THIS BETTER - FIX __str__ for None or fix init to replace None with False
                self.matrix = 0
                self.level = 0
                self.multiplier = 0
                self.source = False
                self.destination = False

            # - If not ACK/NAK then extract the payload:
            else:
                # TODO - this will fail if it's a command we don't recognise...
                self.command = list(utils.COMMANDS.keys())[list(utils.COMMANDS.values()).index(self.encoded[utils.COMMAND_BYTE])]
                self.matrix, self.level = utils.decode_matrix_level(self.encoded)

                if self.command in ("connect", "connected"):
                    self.multiplier = self.encoded[utils.MULTIPLIER_BYTE]
                    self.source, self.destination = utils.decode_source_destination(self.encoded)

                elif self.command in ("push_labels", "push_labels_extended"):
                    self.multiplier = 0
                    self.source = False
                    self.destination = utils.get_labels_destination(self.encoded)
                    # - TODO parse encoded labels (but only for the benefit of the virtual_router, as we only send,
                    # -      and do not receive label messages
                    self.labels = "True"
                    # self.labels = utils.get_labels()

                elif self.command in ("cross-point tally dump (byte)",
                                      "cross-point tally dump (word/extended)"):
                    # TODO, jsut focusing on the word/extended, will have to do the short one separately
                    self.matrix, self.level = utils.decode_matrix_level(self.encoded) # - TODO dont need to do this here, set above

                    # TODO need to set multiplier, check its the same byte as connect command or adjust

                    self.tallies = self.encoded[utils.COMMAND_BYTE + 2]

                    # TODO - parse id based on multiplier, div & mod,
                    #        HERE IM JUST USING MOD SO WILL FAIL FOR BIGGER NUMBERS!!
                    self.destination = self.encoded[utils.COMMAND_BYTE + 4]
                    self.source = self.encoded[utils.COMMAND_BYTE + 6]

                    # TODO PARSE remaining message for potential extra sources??...
                    # get byte count ...

        else:
            #print("[swp_message.__init__]: command = {}, source = {}, destination = {}".format(command, source, destination))
            self.command = command

            if matrix is not None and level is not None:
                # - Matrix & level have been passed to the constructor as discrete values
                # - (rather than as part of source/dest node objects)
                self.matrix = matrix
                self.level = level
            else:
                self.matrix, self.level = destination.matrix, destination.level

            if source is not None:
                if type(source) is int:
                    self.source = source
                else:
                    self.source = source.id
            else:
                self.source = False

            if destination is not None:
                if type(destination) is int:
                    self.destination = destination.id
                else:
                    self.destination = destination.id

            else:
                self.destination = False # TODO, probs dont need this now, just leave as None

            if self.command in ("connect", "connected"):
                self.multiplier = utils.encode_multiplier(self.source, self.destination)

            if self.command in ("push_labels", "push_labels_extended"):
                self._char_len = utils.CHAR_LEN_CODES[char_len]
                self.labels = set_label_len(labels, char_len)
                self.multiplier = False
            else:
                self.labels = False

            self.encoded = self._encode()

        #self.summary = self._get_summary()
        self.summary = self._summary()

    def __str__(self):
        return "SWP08 Message object - Command: {}, Matrix: {}, Level: {}, Multiplier: , Source: {}, Destination: {}," \
               "\nLabels: {}\nEncoded: {}".format(self.command, self.matrix, self.level, #self.multiplier,
                                                  self.source, self.destination, self.labels, self.encoded)

    def _summary(self):
        summary = self.command.upper()
        if self.command in ("connect", "connected"):

            #if type(self.source) is int:
            #    summary += " Matrix: {}, Level: {}, Source: {}, Destination: {}".format(self.matrix, self.level,
            #                                                                            self.source, self.destination)

            #else:
            #    summary += " Matrix: {}, Level: {}, Source: {}, Destination: {}".format(self.matrix, self.level,
            #                                                                            self.source, self.destination)

            summary += " Matrix: {}, Level: {}, Source: {}, Destination: {}".format(self.matrix, self.level,
                                                                                    self.source, self.destination)
        elif self.command in ("push_labels", "push_labels_extended"):
            summary += " First Destination: {}, Label/s: {}".format(self.destination, self.labels)

        elif self.command == "cross-point tally dump request":
            summary += " Matrix: {}, Level: {}".format(self.matrix, self.level)

        elif self.command in ("cross-point tally dump (byte)", "cross-point tally dump (word/extended)"):
            summary += " Matrix: {}, Level: {}, Dest: {}, Src:{}".format(self.matrix, self.level, self.destination, self.source)

        return summary


    """ PUBLIC CONSTRUCTORS FOR INSTANTIATING THIS CLASS """
    @classmethod
    def connect(cls, source, destination):
        """
        Instantiate a connection Message object
        :param source: Node object with node.io_type of 'source'
        :param destination: Node object with node.io_type of 'destination'
        :return: SWP08 Message object for connecting a source to a destination
        """
        message = Message(command="connect", source=source, destination=destination)
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

    @classmethod
    def push_labels(cls, labels, first_destination, char_len=12):
        """
        Instantiate a label push message object
        :param labels: list of strings
        :param first_destination: int - ID of first destination (if multiple labels passed,
                                        they will be applied to consecutive destination IDs
        :param char_len: int - 4, 8, 12, 16 or 32 character labels are supported
        :param matrix: int
        :param level: int
        :param multiplier: int
        :return: SWP message object for pushing labels
        """
        #message = Message(command="push_labels", labels=labels, destination=first_destination.id, char_len=char_len,
        #                  matrix=first_destination.matrix, level=first_destination.level, multiplier=multiplier)

        message = Message(command="push_labels", labels=labels, destination=first_destination, char_len=char_len)

        return message

    @classmethod
    def push_labels_extended(cls, labels, first_destination, char_len=4, matrix=0, level=0, multiplier=0):
        """
        Instantiate an extended label push message object
        # TODO - understand nature of 'extended'... it supports a larger number of IDs?
        :param labels: list of strings
        :param first_destination: int - ID of first destination (if multiple labels passed,
                                        they will be applied to consecutive destination IDs
        :param char_len: int - 4, 8, 12, 16 or 32 character labels are supported
        :param matrix: int
        :param level: int
        :param multiplier: int
        :return: SWP message object for pushing labels
        """
        message = Message(command="push_labels_extended", labels=labels, destination=first_destination,
                          char_len=char_len,
                          matrix=matrix, level=level, multiplier=multiplier)
        return message

    @classmethod
    def cross_point_tally_dump_request(cls, matrix=0, level=0):
        message = Message(command="cross-point tally dump request", matrix=matrix, level=level)
        return message

    """ PRIVATE METHODS """
    def _encode(self):
        """
            Encodes message params into SWP08 protocol byte string
            SWP08 message format - SOM, DATA, BTC, CHK, EOM
            :return: SWP08 encoded byte string, ready to send to mixer
        """
        matrix_level = utils.encode_matrix_level(self.matrix, self.level)
        command = [utils.COMMANDS[self.command], matrix_level]

        if self.command in ("connect", "connected"):
            data = command + [self.multiplier, self.destination % 128, self.source % 128]

        elif self.command in ("push_labels", "push_labels_extended"):
            start_dest_div = int(self.destination / 256)
            start_dest_mod = self.destination % 256
            label_qty = len(self.labels)
            labels = format_labels(self.labels)
            data = command + [self._char_len, start_dest_div, start_dest_mod, label_qty] + labels

        elif self.command == "cross-point tally dump request":
            data = command

        else:
            print("[swp_message._encode]: unsupported command: {}".format(self.command))
            return False

        byte_count = len(data)
        data.append(byte_count)
        checksum = utils.calculate_checksum(data)

        # New - should escape any dles in payload.
        # data = bytes(data)
        # data = data.replace(b'\x10', b'\x10\x10')
        # data = list(data)

        message = utils.SOM + data + [checksum] + utils.EOM

        return bytes(message)

    def _get_summary(self):
        # - TODO - think this can be removed,
        if self.labels:
            labels = '\n  Labels: '
            labels += ''.join(self.labels)
        else:
            labels = ''



        r = ['Command: {}, [Matrix:{}, Level:{}] '
             'Source:{}, Destination: {}{}'.format(self.command.upper(),
                                                   self.matrix,
                                                   self.level,
                                                   self.source,
                                                   self.destination,
                                                   labels)]
        return r


if __name__ == '__main__':
    heading = "SWPO8 Router Control Message Encoding and Decoding"
    header_width = len(heading) + 8
    print("\n{}\n -- {} --\n{}".format(header_width * '#', heading, header_width * '-'))

    # - Test message decode - Sample "Connected" message received from mixer:
    connected_message = b'\x10\x02\x04\x00\x00\n\x00\x05\xed\x10\x03'
    test = Message.decode(connected_message)
    print("\nTest message decode using a sample 'Connected' message received from a mixer...\n{}".format(test))

    # - Test message encode - connect source ID 1 to destination ID 11
    # - Note, ID "1" in Calrec UI/csv == 0 in protocol/message
    #test = Message.connect(0, 10)
    #print("\nTest message encode, connect source 0 to dest 10...\n{}".format(test))

    # - Test decode of above encode
    test2 = Message.decode(test.encoded)
    print("\nTest decoding of the previously encoded message...")
    print("Decode == Encode:", print(test) == print(test2))

    # - Test push_labels message
    labels = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
    #test = Message.push_labels(labels, 0)
    #print("\nTest push_labels message...\n{}".format(test))

    # - Test push_labels message, set to 8 chars
    labels = ["testing", "eight", "char", "labels", "so", "some very long"]
    #test = Message.push_labels(labels, 0, char_len=8)
    #print("\nTest 8 character push_labels message...\n{}".format(test))

    # - Test push_labels_extended
    labels = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
    #test = Message.push_labels_extended(labels, 0)
    #print("\nTest push_labels_extended message...\n{}".format(test))

    # - Test cross-point tally dump request
    matrix, level = 0, 0
    msg = Message.cross_point_tally_dump_request(matrix, level)
    print(msg)
    print(msg.summary)
    print(header_width * "-")
