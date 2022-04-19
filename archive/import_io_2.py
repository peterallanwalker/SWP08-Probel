# - import source and destinations Calrec csv files.

import csv

import cli_utils

TITLE = "Import IO"
VERSION = 0.1


def import_io_from_csv(csv_file):
    """
    :param csv_file: calrec format IO/SWP csv file
    :return: dictionary - sources, source IDs as keys,
                          Desinations, dest IDs as keys
    TODO - might need to key by Matrix-Level-ID but only handling matrix/level 0 at moment
    TODO - These get initliased at start up then passed around a lot, so maybe cut out the unused data
            ... like in v1... that will also sanitize may keys
            ... and make the keys ints not strings
    """
    sources = {}
    destinations = {}

    with open(csv_file, 'r') as data:

        for line in csv.DictReader(data):
            source_id = line['EDIT Out SW-P-08 ID']
            destination_id = line['EDIT In SW-P-08 ID']
            if source_id:
                sources[source_id] = line

            if destination_id:
                destinations[destination_id] = line

    return sources, destinations


def parse_io(line, io):
    r = {'group': line['Virtual Patchbay Name'],
         'channel': line['Patch Point Number'],
         'label': line['EDIT Patch Point User Label']}

    if io == 'source':
        r['matrix'] = line['EDIT Out SW-P-08 Matrix']
        r['level'] = line['EDIT Out SW-P-08 Level']
        r['id'] = line['EDIT Out SW-P-08 ID']

    elif io == 'destination':
        r['matrix'] = line['EDIT In SW-P-08 Matrix']
        r['level'] = line['EDIT In SW-P-08 Level']
        r['id'] = line['EDIT In SW-P-08 ID']

    return r


if __name__ == '__main__':

    cli_utils.print_header(TITLE, VERSION)
    csv_file = "../VirtualPatchbays.csv"

    sources, destinations = import_io_from_csv(csv_file)

    print("SOURCES:")
    for source in sources:
        print("source id:", source, ":", sources[source])

    print("\nDESTINATIONS:")
    for destination in destinations:
        print("destination id:", destination, ":", destinations[destination])

    print("Source qty:", len(sources))
    print("Destinations qty:", len(destinations))
