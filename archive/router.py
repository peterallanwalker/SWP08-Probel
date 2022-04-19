# - Data model & comms interface to sit between UI and router.
# - Peter Walker, April 2022

import cli_utils
from connection import Connection
from swp_message import Message

TITLE = 'Router'
VERSION = 0.1


class Io:
    def __init__(self, swp_id, matrix, level, group, ch, label, user_label):
        self.matrix = matrix
        self.level = level
        self.id = swp_id
        self.group = group
        self.ch = ch
        self.label = label
        self.user_label = user_label

    def __str__(self):
        return "IO object: Matrix:{}, Level:{}, ID:{}, Label:{}, User Label:{}".format(self.matrix, self.level,
                                                                                       self.id, self.label,
                                                                                       self.user_label)


class Source(Io):
    def __init__(self, swp_id, matrix=0, level=0,
                 group='', ch='', label='', user_label=''):
        super().__init__(swp_id, matrix, level,
                         group, ch, label, user_label)

        self.connected_source_label = None

    def __str__(self):
        connected_source = ''
        if self.connected_source_label:
            connected_source = "Connected Source Label: {}".format(self.connected_source_label)
        return "SOURCE: {}, {}".format(super().__str__(), connected_source)


class Destination(Io):
    def __init__(self, swp_id, matrix=0, level=0,
                 group='', ch='', label='', user_label=''):
        super().__init__(swp_id, matrix, level,
                         group, ch, label, user_label)

        self.connected_source = None

    def __str__(self):
        connected_source = ''
        if self.connected_source:
            connected_source = "Connected Source: {}".format(self.connected_source)
        return "DESTINATION: {}, {}".format(super().__str__(), connected_source)


class Router:
    def __init__(self, settings, io):
        self.connection = Connection(settings["Router IP Address"], settings["Port"], settings["Protocol"])
        self.io = io

        # Set up connection state for each dest... TODO - read-back the actual state from the router on startup
        for dest in self.io['destinations']['1']['1']:
            self.io['destinations']['1']['1'][dest]["connected source"] = False  # TODO - use digital silence,

        # initialise connected source label
        for src in self.io['sources']['1']['1']:
            self.io['sources']['1']['1'][src]["connected source label"] = False

    def process_incoming_messages(self):
        """ Process any messages received on the connection
            CALL THIS PERIODICALLY, PROB FROM GUI LOOP, or maybe put a thread here.
            ... or limit max  time
        """
        while self.connection.receive_buffer_len():

            print("[connectIO_prot_gui.process_incoming messages]: Messages in receive buffer:",
                  self.connection.receive_buffer_len())

            msg = Message.decode(self.connection.get_message())

            # TODO - push ACK NAK back to sender & have them wait/retry
            if msg.command == 'ACK':
                print("[connectIO_prot_gui.process_incoming messages]: >>> ACK received")
            elif msg.command == "NAK":
                print("[connectIO_prot_gui.process_incoming messages]: >>> ** NAK ** received!")
            else:
                msg.print_summary("[connectIO_prot_gui.process_incoming messages]: >>> Received Message:")
                # print("Message received "
                #      "from router:", response)
                self._update_data(msg)

    def _update_data(self, message):
        """
        Takes pre-validated SWP message received from the router, updates the data model to reflect
        """
        # TODO - parse connect differently / controller
        #  should not receive it but its all my virtual router outputs at mo
        if message.command in ('connected', 'connect'):
            print("[interface.update_data]: connect/connected received, destination:", message.destination)
            # - TODO - optimise data so I dont have to loop to find the right ID, and error check against duplicate IDs,
            # - (on other matrix/level as well as erroneous)
            self.io['destinations']['1']['1'][str(message.destination)]["connected source"] = str(message.source)

            print("updated data", self.io['destinations']['1']['1'][str(message.destination)])

    def _get_first_connected_destination(self, source, matrix=0, level=0):
        """
        Used when a connected source label is changed, to push the label to the connected destination.
        ... Only currently getting & sending the first connected destination of the given source
            The Calrec router checks its own destinations and will update the labels of all connected
            that are from the same source (not sure if that behaviour can be relied upon for non-calrec devices,
            may need to push a separate label message for each connected destination when integrating with other
            implementations... As many labels & destinations can be passed in a single SWP message,
            it may be more efficient to periodically push labels to all destinations rather than selectively on change
            & connection as we are currently.
        :param source: int
        :param matrix: int
        :param level: int
        :return: int
        """
        for dest in self.io['destinations']['1']['1']:
            if self.io['destinations']['1']['1'][dest]['connected source'] == source:
                return dest

    # --------------------------------- #
    # - PUBLIC METHODS, CALLED BY GUI - #

    def make_connection(self, source, destination, matrix=0, level=0):
        """
        To be called by the GUI/controller
        :param matrix: int
        :param level: int
        :param source: int
        :param destination: int
        :param label: str (optional)
        :param char_len int (optional)
        :return: True if ACK response received, False if no response or NAK
        """
        # - TODO, how to handle ACK/NAK / retry timeout without blocking GUI, and without dumping or missing messages.
        # - ... that should all be handled by Connection, not here!
        self.connection.send(Message.connect(source, destination, matrix, level).encoded)
        # TODO - update data model, so store connected source labels, maybe create a source and dest class
        #if label:
        #    self.connection.send(Message.push_labels([label], destination, char_len, matrix, level).encoded)

    def update_source_label(self, source, label):

        dest = self._get_first_connected_destination(source)
        print('[interface, updating source labels', dest)
        if dest:
            self.connection.send(Message.push_labels([label], int(dest)).encoded)


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)

    source = Source(1, 1, 1, group="group1", ch="1", label="label", user_label="my src")
    dest = Destination(2, 2, 2, group="group2", ch="2", label="dest label", user_label='my dest')

    print(source)
    print(60 * '-')
    print(dest)

    io = import_io
