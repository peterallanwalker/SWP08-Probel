# SWP08
# For encoding and decoding to SWP08 router control messages
# Peter Walker, June 2021

# SWP08 protocol info:
# https://wwwapps.grassvalley.com/docs/Manuals/sam/Protocols%20and%20MIBs/Router%20Control%20Protocols%20SW-P-88%20Issue%204b.pdf

import swp_utils_01 as utils


class Message:

    def __init__(self,
                 command=None,
                 matrix=None,
                 level=None,
                 multiplier=None,
                 source=None,
                 destination=None,
                 source_label=None,
                 encoded=None,):
        """
            *** NOT INTENDED TO BE CALLED DIRECTLY, INSTANTIATE USING THE CLASS METHODS... ***
            - e.g call Message.connect(source, destination) to instantiate a connect message using source/dest values
            - or call Message.decode(msg byte string) to instantiate a message object from its encoded form.
        """
        if encoded:
            # we will be pre-validating received messages so dont want to waste time error checking here

            # TODO -decode
            self._encoded = encoded
            self._command = list(utils.COMMANDS.keys())[list(utils.COMMANDS.values()).index(self._encoded[utils.COMMAND_BYTE])]
            
            if self._command in ("connect", "connected"):
                # TODO - handle different matrix, level and multiplier
                self._matrix = 0
                self._level = 0
                self._multiplier = 0
                self._source = self._encoded[utils.SOURCE_BYTE]
                self._destination = self._encoded[utils.DESTINATION_BYTE]
            

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
        return "SWP08 Message object - Command: {}, Matrix: {}, Level: {}, Multiplier: {}, Source: {}, Destination: {}, Label: {}, Encoded: {}".format(self._command, self._matrix, self._level, self._multiplier, self._source, self._destination, self.source_label, self._encoded)

    """ PUBLIC CONSTRUCTORS FOR INSTANTIATING THIS CLASS """
    @classmethod
    def connect(cls, source, destination, source_label=None, matrix=0, level=0, multiplier=0):
        """
        Instantiate a connection Message object
        :param source:
        :param destination:
        :param source_label:
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

    """ PRIVATE METHODS """
    def _encode(self):
        """
            Encodes message params into SWP08 protocol byte string
            SWP08 message format - SOM, DATA, BTC, CHK, EOM
            :return: SWP08 encoded byte string, ready to send to mixer
        """

        data = [utils.COMMANDS[self._command]] + [self._matrix, self._multiplier, self._destination, self._source]
        byte_count = len(data)
        #print("DEBUG byte count:", byte_count)
        data.append(byte_count)
        checksum = utils.calculate_checksum(data)

        message = utils.SOM + data + [checksum] + utils.EOM
        #print("DEBUG message", message)
        return bytes(message)




if __name__ == '__main__':

    print(20 * '#' + ' SWP08 ' + 20 * '#')

    # Test message - connect source 0 to destination 10
    test1 = Message.connect(1, 11)
    print("Test message:", test1)

"""
    # Sample message from mixer - Connected
    test_message = b'\x10\x02\x04\x00\x00\n\x00\x05\xed\x10\x03'
    test2 = Message.decode(test_message)
    print("Test decoding:", test2)
"""