# - SWP08/Probel router emulator
# - A virtual router for testing SWP controller when no real router available
# - Peter Walker, June 2022

import os
import datetime

import cli_utils
import swp_utils
from import_io import import_io_from_csv
from socket_connection_manager import Server
import swp_message as swp_message
import swp_node

TITLE = "SWP08/Probel Router Emulator"
VERSION = 1.2
LOCALHOST = '127.0.0.1'
CONFIG_FILE = 'emulator_settings.txt'


def prompt_for_csv_file():
    """ Print all csv files in same folder as this file
        prompt user to choose one and return the filename
    """
    # Search for csv files and add them to a dict
    csv_files = {}
    i = 1
    for file in os.listdir():
        if file.endswith(".csv"):
            csv_files[i] = file
            i += 1

    for k, v in csv_files.items():
        print(k, "-", v)

    return csv_files[int(input("\nSelect a csv file for the I/O: "))]


class Router:
    def __init__(self, server_connection, io_csv):
        self.connection = server_connection
        self.io_csv = io_csv
        self.sources, self.destinations = import_io_from_csv(self.io_csv)

    def process_incoming_messages(self):
        while len(self.connection.messages):

            timestamp, message = self.connection.get_received_message()  # - pops oldest message off the receive buffer
            message = swp_message.decode(message)

            # - Output to terminal
            swp_utils.print_message(timestamp, "received", message)

            # - Messages in the connection's receive buffer are pre-validated by checksum
            # - so send an acknowledgement of receipt
            response = swp_message.Response("ACK")
            swp_utils.print_message(datetime.datetime.now(), "sending", response)
            self.connection.send_message(response)

            if message.command == "connect":
                destination = swp_utils.match_destination(message, self.destinations)
                source = swp_utils.match_source(message, self.sources)

                if destination and source:
                    destination.connected_source = source
                    response = swp_message.Connected(source, destination)
                    swp_utils.print_message(datetime.datetime.now(), "sending", response)
                    connection.send_message(response)

                else:
                    if not destination:
                        print(f"[{TITLE}.process_incoming_messages]: No destination for matrix {message.matrix}, "
                              f"level {message.level}, id {message.destination} in {self.io_csv}")
                    if not source:
                        print(f"[{TITLE}.process_incoming_messages]: No source for matrix {message.matrix}, "
                              f"level {message.level}, id {message.source} in {self.io_csv}")

            elif message.command in ('push_labels', 'push_labels_extended'):
                print(f'[{TITLE}.process_incoming_messages]:Label/s received')
                # TODO Apply labels to self.destinations

            elif message.command == 'cross-point tally dump request':
                print(f'[{TITLE}.process_incoming_messages]:Cross-point tally dump request received for '
                      f'matrix:{message.matrix}, level:{message.level}')
                consecutive_destinations = swp_node.get_consecutive_nodes(self.destinations, matrix=message.matrix, level=message.level)

                for destinations in consecutive_destinations:
                    response = swp_message.CrossPointTallyDumpWord(destinations)
                    swp_utils.print_message(datetime.datetime.now(), "sending", response)
                    connection.send_message(response)

            else:
                print(f'[{TITLE}.process_incoming_messages]:Message type unsupported: {message.command}')


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)

    # - Check to see if there is a config file
    try:
        with open(CONFIG_FILE, "r") as f:
            io_filename = f.readline()
    except FileNotFoundError:
        # if there's no config file, ask the user which IO csv file they want to use
        io_filename = prompt_for_csv_file()

    # - Check they want to use this file
    accept = input(f"Use {io_filename}? (y/n): ")
    if accept.lower() not in ("yes", "y", ""):
        # - Allow them to select a different file
        io_filename = prompt_for_csv_file()

        # - Save IO csv filename to a config txt file for next time the program is run
        with open(CONFIG_FILE, 'w') as f:
            f.write(io_filename)

    connection = Server(LOCALHOST)
    router = Router(connection, io_filename)

    print("Sources:")
    for src in router.sources:
        print(src)
    print("Destinations:")
    for dst in router.destinations:
        print(dst)

    print("Listening for client connections...")
    while True:
        router.process_incoming_messages()
