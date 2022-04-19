# - Provides the Node class to represent SWP sources & destinations
# -    (Note each node represents either a source or a destination, entities with both source and
# -     destination IDs shall be represented by two separate Nodes.
# -
# - Provides import_io_from_csv to take a Calrec format SWP CSV files and return as a dict of nodes
# - with the dict sorted by Matrix, Level, Sources & Destinations
# -
# - Peter Walker, April 2022

import cli_utils

TITLE = "SWP Node"
VERSION = 0.2


class Node:
    """
    Represents an SWP node - an individual Source OR Destination.
    (note an entity with both source and destination IDs should be represented as two separate nodes)
    """
    def __init__(self, matrix, level, swp_id, group, ch, label, user_label, io_type):
        self.matrix = matrix
        self.level = level
        self.id = swp_id
        self.group = group
        self.ch = ch
        self.label = label
        self.user_label = user_label
        self.type = io_type
        self.connected_source = None

    """ PUBLIC CONSTRUCTORS """
    @classmethod
    def source(cls, swp_id, matrix, level, group, ch, label, user_label):
        node = Node(swp_id, matrix, level, group, ch, label, user_label, 'source')
        return node

    @classmethod
    def destination(cls, swp_id, matrix, level, group, ch, label, user_label):
        node = Node(swp_id, matrix, level, group, ch, label, user_label, 'destination')
        return node

    def __str__(self):
        connected_source = ''
        if self.connected_source:
            connected_source = 'Connected Source:{}'.format(self.connected_source)
        return "[swp_node object]:{} - Matrix:{}, Level:{}, ID:{}, Label:{}, User Label:{}".format(self.type,
                                                                                                   self.matrix,
                                                                                                   self.level,
                                                                                                   self.id,
                                                                                                   self.label,
                                                                                                   self.user_label,
                                                                                                   connected_source)


if __name__ == '__main__':

    cli_utils.print_header(TITLE, VERSION)

    source = Node.source(1, 2, 3, "group label", "channel label", "node label", "user label")
    destination = Node.destination(4, 5, 6, "group label", "channel label", "node label", "user label")

    print(source)
    print(destination)
