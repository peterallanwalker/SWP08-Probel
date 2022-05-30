# - Utility tools for CLI based "TUI"
# Peter Walker, April 2022

from string import punctuation

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


def print_block(heading='', rows=()):
    width = len(heading)
    row_width = len(max(rows, key=len))
    if row_width > width:
        width = row_width

    print("{}\n{}".format(width * '-', heading))
    for row in rows:
        print(row)
    print("\n")


def get_number(prompt='number'):
    """
    cli prompt user until they input a number
    :param prompt: optional string for the prompt to describe the number being asked for
    :return: int, from user input.
    """
    # - prompt user to input a number, repeat until they do and return the number as an int
    while True:
        n = input("Enter " + prompt + ": ").split()
        if len(n) == 1 and n[0].strip(punctuation).isnumeric():
            return int(n[0].strip(punctuation))


if __name__ == '__main__':
    print_header(TITLE, VERSION)

    block_header = "Heading"
    content = ["Row 1", "Row 2", "Row 3", "Row 4"]
    print_block(block_header, content)


