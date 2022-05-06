# - Imports Calrec formatted SWP/VPB CSV files,
# - V05 - changed to return a tuple of (source_nodes, destination_nodes)
# -       (previously returned a complicated nested dict sorted by matrix & level with additional ID keys
# -        ... changing this makes lookup simpler but needs UI to filter matrix/levels
#
# - Peter Walker, April 2022
#
# - TODO, check handling of invalid csv files

import csv

import cli_utils
from swp_node_02 import Node

TITLE = "Import IO"
VERSION = 0.6


# - PRIVATE FUNCTIONS USED BY import_io_from_csv
def _parse_line(line, io_nodes):
    """
    Parses a line from the CSV, adds to io_nodes tuple
    :param line: csv line (from a Calrec formatted IO/VPB CSV export)
    :param r: tuple (list of source nodes, list of destination nodes
    :return: r - the modified tuple (!)
    """
    source_id = line['EDIT Out SW-P-08 ID']
    destination_id = line['EDIT In SW-P-08 ID']

    if source_id:
        io_nodes[0].append(_csv_line_to_node(line, "source"))
    if destination_id:
        io_nodes[1].append(_csv_line_to_node(line, "destination"))
    return io_nodes


def _csv_line_to_node(line, io_type):
    """
    :param line: line from calrec formatted csv file
    :param io_type: str "source" or "destination"
    :return: Node object representing the source/destination from the csv line

    Note, If a line represent both source and destination, it should be passed twice to create two separate nodes
    """
    if io_type == 'source':
        prefix = 'EDIT Out SW-P-08 '
    else:
        prefix = 'EDIT In SW-P-08 '

    if io_type == 'source':
        return Node.source(int(line[prefix + 'Matrix']) - 1,
                           int(line[prefix + 'Level']) - 1,
                           int(line[prefix + 'ID']) - 1,
                           line['Virtual Patchbay Name'],
                           line['Patch Point Number'],
                           line['Patch Point Default Label'],
                           line['EDIT Patch Point User Label'])

    elif io_type == 'destination':
        return Node.destination(int(line[prefix + 'Matrix']) - 1,
                                int(line[prefix + 'Level']) - 1,
                                int(line[prefix + 'ID']) - 1,
                                line['Virtual Patchbay Name'],
                                line['Patch Point Number'],
                                line['Patch Point Default Label'],
                                line['EDIT Patch Point User Label'])

    else:
        return False


# - PUBLIC FUNCTIONS - #
def import_io_from_csv(csv_file):
    """
    :param csv_file: filename of local calrec format IO/SWP csv file
    :return: tuple of source_nodes, destination_nodes
    """
    source_nodes = []
    destination_nodes = []
    io_nodes = (source_nodes, destination_nodes)

    with open(csv_file, 'r') as data:
        for line in csv.DictReader(data):
            io_nodes = _parse_line(line, io_nodes)

    return io_nodes


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)
    csv_file = "VirtualPatchbays.csv"

    io = import_io_from_csv(csv_file)

    print("SOURCES")
    for i in io[0]:
        print(i)
    print("DESTINATIONS")
    for i in io[1]:
        print(i)
