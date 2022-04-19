# - Imports Calrec formatted SWP CSV files,
# - returns a dict of Node objects sorted by Matrix, Level, Sources & Destinations:
#       {'matrices': {<n> :
#           {'level': {<n>:
#               {'sources': {'<id>': Node object}
#               {'destinations': {'<id>': Node object}
#           }
#       }
# - Peter Walker, April 2022

import csv

import cli_utils
from swp_node import Node

TITLE = "Import IO"
VERSION = 0.4


# - PUBLIC FUNCTION - #
def import_io_from_csv(csv_file):
    """
    :param csv_file: filename of local calrec format IO/SWP csv file
    :return: dictionary - {'matrices': {<n> :
                              {'level': {<n>:
                                  {'sources': {'<id>': Node object}
                                  {'destinations': {'<id>': Node object}
                              }
                           }
    """
    # - Initialise the dict
    r = {'matrix': {}}

    with open(csv_file, 'r') as data:
        for line in csv.DictReader(data):
            r = _parse_line(line, r)

    return r


def print_io(d, indent=0):
    for key, value in d.items():
        print('  ' * indent + str(key))
        if isinstance(value, dict):
            print_io(value, indent+1)
        else:
            print('  ' * (indent+1) + str(value))


# - PRIVATE FUNCTIONS USED BY import_io_from_csv
def _parse_line(line, r):
    """
    Parses a line from the CSV, adds to dict r
    :param line: csv line (from a Calrec formatted IO/VPB CSV export)
    :param r: dict supplied by import_io_from_csv()
    :return: r - the modified dict
    """
    source_id = line['EDIT Out SW-P-08 ID']
    destination_id = line['EDIT In SW-P-08 ID']

    if source_id:
        r = _update_dict(line, r, "source")
    if destination_id:
        r = _update_dict(line, r, "destination")
    return r


def _update_dict(line, r, io_type):
    """
    :param line: line from Calrec formatted swp csv file via csv.dictReader
    :param r: dict of IO
    :param io_type: string "sources" or "destinations"
    :return: updated dict
    """

    if io_type == 'source':
        prefix = 'EDIT Out SW-P-08 '
    else:
        prefix = 'EDIT In SW-P-08 '

    # TODO, this feels hacky, should be a neater way maybe with isInstance recursively
    # Check if keys already exist, create them if not
    try:
        test = r['matrix'][int(line[prefix + 'Matrix'])]
    except KeyError:
        r['matrix'][int(line[prefix + 'Matrix'])] = {'level': {}}
    try:
         test = r['matrix'][int(line[prefix + 'Matrix'])]['level'][int(line[prefix + 'Level'])]
    except KeyError:
        r['matrix'][int(line[prefix + 'Matrix'])]['level'][int(line[prefix + 'Level'])] = {}
    try:
        test = r['matrix'][int(line[prefix + 'Matrix'])]['level'][int(line[prefix + 'Level'])][io_type]
    except KeyError:
        r['matrix'][int(line[prefix + 'Matrix'])]['level'][int(line[prefix + 'Level'])][io_type] = {}
    try:
        test = r['matrix'][int(line[prefix + 'Matrix'])]['level'][int(line[prefix + 'Level'])][io_type][int(line[prefix + 'ID'])]
        print("[import_io.parse_line]: ** WARNING ** - Duplicate Matrix {}, Level {}, ID {} already parsed"
              " - Check your CSV for duplicates.".format(line[prefix + 'Matrix'],
                                                         line[prefix + 'Level'],
                                                         line[prefix + 'ID']))
    except KeyError:
        if io_type == 'source':
            node = Node.source(int(line[prefix + 'Matrix']),
                               int(line[prefix + 'Level']),
                               int(line[prefix + 'ID']),
                               line['Virtual Patchbay Name'],
                               line['Patch Point Number'],
                               line['Patch Point Default Label'],
                               line['EDIT Patch Point User Label'])
        else:
            node = Node.destination(int(line[prefix + 'Matrix']),
                                    int(line[prefix + 'Level']),
                                    int(line[prefix + 'ID']),
                                    line['Virtual Patchbay Name'],
                                    line['Patch Point Number'],
                                    line['Patch Point Default Label'],
                                    line['EDIT Patch Point User Label'])

        r['matrix'][int(line[prefix + 'Matrix'])]['level'][int(line[prefix + 'Level'])][io_type][int(line[prefix + 'ID'])] = node

    return r


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)
    csv_file = "VirtualPatchbays.csv"

    io = import_io_from_csv(csv_file)

    print_io(io)


