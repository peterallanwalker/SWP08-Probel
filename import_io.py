# - import source and destinations Calrec csv files.

import csv

import cli_utils

TITLE = "Import IO"
VERSION = 0.1


def import_io_from_csv(csv_file):

    sources = []
    destinations = []

    with open(csv_file, 'r') as data:

        for line in csv.DictReader(data):

            if line['EDIT Out SW-P-08 ID']:
                sources.append(parse_io(line, 'source'))
            if line['EDIT In SW-P-08 ID']:
                destinations.append(parse_io(line, 'destination'))

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

    csv_file = "VirtualPatchbays.csv"

    sources, destinations = import_io_from_csv(csv_file)

    print("SOURCES:")
    for source in sources:
        print(source)

    print("\nDESTINATIONS:")
    for destination in destinations:
        print(destination)

    print("Source qty:", len(sources))
    print("Destinations qty:", len(destinations))
