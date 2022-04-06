# - Utility tools for CLI based "TUI"
# Peter Walker, April 2022

# Just gives me consistent header formatting at the mo
# TODO, add other common CLI formatting as and when I need it moving forwards
# TODO, use curses for more advance terminal manipulation, colour/highlights, clear/overwrite/cursor movement
# TODO, e.g. for progress bars etc

TITLE = "Command Line Utilities"
VERSION = 1.0


def print_header(title, version=None):
    """
    Prints a formatted header
    :param title: string
    :param version: float
    :return:
    """
    if version:
        version = " v" + str(version)

    heading = title + version
    header_width = len(heading) + 8
    print("\n{}\n -- {} --\n{}".format(header_width * '#', heading, header_width * '-'))


def print_block(heading='', rows=None):
    if rows is None:
        rows = []
    width = len(heading)
    row_width = len(max(rows, key=len))
    if row_width > width:
        width = row_width
    width *= 2
    print("\n{}\n -- {} --\n{}".format(width * '=', heading, width * '-'))
    for row in rows:
        print(" ", row)
    print(width * '-')


if __name__ == '__main__':
    print_header(TITLE, VERSION)

    block_header = "Heading"
    rows = ["Row 1", "Row 2", "Row 3", "Row 4"]
    print_block(block_header, rows)
