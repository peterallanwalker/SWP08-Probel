# - Data model & comms interface to sit between UI and the router/socket connection with the router.
# - Peter Walker, April 2022
import time  # - Just for debug

import cli_utils
from import_io import import_io_from_csv
import settings as config
from client_connection import Connection
import swp_message as message
from message_log import Logger
from swp_utils import match_destination, match_source

TITLE = 'SWP Router'
VERSION = 0.6


class Router:
    # TODO - Added a temporary optional io+config argument as not part of settings in this version
    def __init__(self, settings, io_config=None):
        self.settings = settings
        self.log = Logger()
        self.log.log("test", "test", "test")
        self.connection = Connection(settings["Router IP Address"], settings["Port"], log=self.log)
        #self.connection = Connection(settings["Router IP Address"], settings["Port"])
        if 'IO Config File' in self.settings:
            self.source_data = self.settings['IO Config File']
            self.sources, self.destinations = import_io_from_csv(self.source_data)
        elif io_config:
            self.source_data = io_config
            self.sources, self.destinations = import_io_from_csv(self.source_data)
        else:
            self.source_data = ''
            self.sources = None
            self.destinations = None

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

            #print("[swp_router.process_incoming messages]: Messages in receive buffer:",
            #      self.connection.receive_buffer_len())
            timestamp, msg = self.connection.get_message()
            msg = message.decode(msg)

            self.log.log(timestamp, msg, 'received')
            if msg.command == 'ACK':
                print("[swo_router.process_incoming messages]:{} >>> ACK received".format(timestamp))
            elif msg.command == "NAK":
                print("[swp_router.process_incoming messages]:{} >>> ** NAK received! **".format(timestamp))
            else:
                print("[swp_router.process_incoming messages]:{} >>> Received Message:{}".format(timestamp,
                                                                                                 msg))
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
            destination = match_destination(msg, self.destinations)
            source = match_source(msg, self.sources)
            destination.connected_source = source

    def _get_first_connected_destination(self, source_node):
        """
        Used when a connected source label is changed, to push the label to the connected destination.
        ... Only currently getting & sending the first connected destination of the given source
            The Calrec router checks its own destinations and will update the labels of all connected
            that are from the same source (not sure if that behaviour can be relied upon for non-calrec devices,
            may need to push a separate label message for each connected destination when integrating with other
            implementations... As many labels & destinations can be passed in a single SWP message,
            it may be more efficient to periodically push labels to all destinations rather than selectively on change
            & connection as we are currently.
        """

        for dest in self.destinations:
            if dest.connected_source == source_node:
                print("FIRST CONNECTED DEST:")
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

        #self.connection.send(Message.connect(source.id, destination.id,
        #                                     matrix=source.matrix, level=source.level))

        self.connection.send(message.Connect(source, destination)) # TODO send matrix level

        # - If there is a connected source label for the source, push that to the destination of the external router
        #if self.io['matrix'][source.matrix]['level'][source.level]['source'][source.id].connected_source:
        if source.connected_source:
            self.connection.send(message.PushLabels([source.connected_source], destination, self.label_len))

    def update_source_label(self, source_node, label):
        # print("ROUTER update source label", source_node)
        # - Update the data model
        source_node.connected_source = label

        # - Get the first destination connected to the source if there is one
        destination_node = self._get_first_connected_destination(source_node)

        if destination_node:
            self.connection.send(message.PushLabels([label], destination_node))


def print_io(router):
    print(40 * "-" + "\nSources:")
    for i, node in enumerate(router.sources):
        print(i, node)

    print(40 * "-" + "\nDestinations:")
    for i, node in enumerate(router.destinations):
        print(i, node)


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)

    settings = config.get_settings()  # - present last used settings and prompt for confirm/edit
    config.save_settings(settings)  # - Save user confirmed settings for next startup

    io_config = 'VirtualPatchbays.csv'
    router = Router(settings, io_config=io_config)

    # - Wait for connection
    while router.connection.status != 'Connected':
        pass

    src = router.sources[0]
    dst = router.destinations[0]

    router.connect(src, dst)

    time.sleep(1)
    router.process_incoming_messages()
    print_io(router)

    if router.destinations[0].connected_source == router.sources[0]:
        print("Connect test passed")

    print("\n", router.destinations[0].connected_source)

    print("MESSAGE LOG:")
    print(router.log)
    print("CONNECTION LOG")
    print(router.connection.log)


