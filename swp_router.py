# - Data model & comms interface to sit between UI and router.
# - Peter Walker, April 2022

import time  # - Just for debug

import cli_utils
from import_io import import_io_from_csv
import connectIO_cli_settings as config
from connection_02 import Connection
from swp_message import Message
from message_log import MessageLog

TITLE = 'SWP Router'
VERSION = 0.4


class Router:
    def __init__(self, settings):
        self.settings = settings
        self.log = MessageLog()
        self.connection = Connection(settings["Router IP Address"], settings["Port"],
                                     settings["Protocol"], log=self.log)

        if self.settings['IO Config File']:
            self.source_data = self.settings['IO Config File']
            self.io = import_io_from_csv(self.source_data)
        else:
            self.source_data = ''
            self.io = None

        self.label_len = settings["Label Length"]
        # - TODO - query the router to get the connected source for each desintation
        # - TODO - save/load last entered connected source labels from GUI

    def process_incoming_messages(self):
        """ Process any messages received on the connection
            ... This is currently being called once every GUI loop, getting all received messages since last loop
                    ... Maybe run in a separate thread, either here or in GUI
                    ... Maybe limit max time spent in case loads of messages received?
                    ... (not actually sure what happens if processing takes longer than gui loop refresh interval!)
        """
        while self.connection.receive_buffer_len():

            print("[swp_router.process_incoming messages]: Messages in receive buffer:",
                  self.connection.receive_buffer_len())
            timestamp, msg = self.connection.get_message()
            msg = Message.decode(msg)

            # TODO - push ACK NAK back to sender & have them wait/retry

            self.log.log(timestamp, msg, 'received')
            if msg.command == 'ACK':
                print("[swo_router.process_incoming messages]:{} >>> ACK received".format(timestamp))
            elif msg.command == "NAK":
                print("[swp_router.process_incoming messages]:{} >>> ** NAK ** received!".format(timestamp))
            else:
                msg.print_summary("[swp_router.process_incoming messages]:{} >>> Received Message:".format(timestamp))
                # - Update the data model
                self._update_data(msg)

    def _update_data(self, msg):
        """
        Takes pre-validated SWP message received from the router, updates the data model to reflect
        """
        # Should really parse 'connect' differently to 'connected'
        # (should not receive a connect message from a real router,
        # but that's what my virtual router returns instead of "connected")

        if msg.command in ('connected', 'connect'):
            print("[interface.update_data]: connect/connected received for destination:", msg.destination)
            print("[interface.update_data]: current source:", self.io['matrix'][msg.matrix]['level'][msg.level]['destination'][msg.destination].connected_source)
            self.io['matrix'][msg.matrix]['level'][msg.level]['destination'][msg.destination].connected_source = msg.source
            print("[interface.update_data]: updated destination, new source: {}".format(
                  self.io['matrix'][msg.matrix]['level'][msg.level]['destination'][msg.destination].connected_source))

    def _get_first_connected_destination(self, matrix, level, source_id):
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
        for dest in self.io['matrix'][matrix]['level'][level]['destination']:
            if self.io['matrix'][matrix]['level'][level]['destination'][dest].connected_source == source_id:
                return dest

        return None

    # --------------------------------- #
    # - PUBLIC METHODS - #
    def load_io_config(self, filename):
        self.source_data = filename
        try:
            self.io = import_io_from_csv(filename)

        except KeyError:
            print("[swp_router.load_io_config]: failed to parse csv file, check headers match Calrec csv format")
            # TODO - All tests have been with an Impulse VPB CSV file - check support for Hydra2 based csv files
            return False

        self.settings["IO Config File"] = filename
        return True

    def connect(self, source, destination):
        """
        To be called by the GUI/controller
        :param source_id: Node object with io_type = 'source'
        :param destination: Node object with io_type = 'destination'
        """
        # - TODO, how to handle ACK/NAK / retry timeout without blocking GUI, and without dumping or missing messages.
        # - ... that should all be handled by Connection, not here!
        # - Send connect message to the external router

        if source.matrix != destination.matrix or source.level != destination.level:
            print("[swp_router.connect]: ** ERROR ** "
                  "- Can only connect sources & destinations that are on the same matrix & level")
            return False

        self.connection.send(Message.connect(source.id, destination.id,
                                             matrix=source.matrix, level=source.level).encoded)

        # - If there is a connected source label for the source, push that to the destination of the external router
        #if self.io['matrix'][source.matrix]['level'][source.level]['source'][source.id].connected_source:
        if source.connected_source:
            self.connection.send(Message.push_labels(
                [source.connected_source],
                destination.id, self.label_len, destination.matrix, destination.level).encoded)

    def update_source_label(self, matrix, level, source_id, label):
        # - Update the data model
        self.io['matrix'][matrix]['level'][level]['source'][source_id].connected_source = label
        print('[swp_router.update_source_label]: updated source:',
              self.io['matrix'][matrix]['level'][level]['source'][source_id])

        # - Get the first destination connected to the source if there is one
        dest = self._get_first_connected_destination(matrix, level, source_id)
        if dest:
            self.connection.send(Message.push_labels([label], int(dest)).encoded)


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)

    io_data = 'VirtualPatchbays.csv'  # - Todo - add to settings

    settings = config.get_settings()  # - present last used settings and prompt for confirm/edit
    config.save_settings(settings)  # - Save user confirmed settings for next startup

    #print(io)
    #print(io['matrix'][1]['level'][1]['source'][1])

    router = Router(settings, io_data)

    while router.connection.status != 'Connected':
        pass

    matrix = 1
    level = 1
    router.connect(matrix, level, 1, 11)

    time.sleep(1)

    router.process_incoming_messages()

    router.update_source_label(1, 1, 1, "mylabel")

    time.sleep(1)

    router.process_incoming_messages()

