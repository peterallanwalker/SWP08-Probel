# - Provides the Node class to represent SWP sources & destinations
# -    (Note each node represents either a source or a destination, entities with both source and
# -     destination IDs shall be represented by two separate Nodes.

# - Peter Walker, April 2022

import cli_utils
import swp_utils

TITLE = "SWP Node"
VERSION = 0.4


class Node:
    """
    Represents an SWP node - an individual Source OR Destination.
    (note an entity with both source and destination IDs should be represented as two separate nodes)
    """
    def __init__(self, matrix, level, swp_id, io_type, group="", ch="", label="", user_label=""):
        """
        :param matrix: int
        :param level: int
        :param swp_id: int
        :param io_type: str
        :param group: str
        :param ch:
        :param label: str
        :param user_label: str
        """
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
    def source(cls, matrix, level, id, group='', ch='', label='', user_label=''):
        node = Node(matrix, level, id, 'Source', group=group, ch=ch, label=label, user_label=user_label)
        return node

    @classmethod
    def destination(cls, matrix, level, id, group='', ch='', label='', user_label=''):
        node = Node(matrix, level, id, 'Destination', group=group, ch=ch, label=label, user_label=user_label)
        return node

    def __str__(self):
        group = ''
        ch = ''
        label = ''
        user_label = ''
        connected_source = ''

        if self.connected_source:
            connected_source = ', Connected Source: {}'.format(self.connected_source)
        if self.group:
            group = ', Group: {}'.format(self.group)
        if self.ch:
            ch = ', Channel: {}'.format(self.ch)
        if self.label:
            label = ', Label: {}'.format(self.label)
        if self.user_label:
            user_label = ', User Label: {}'.format(self.user_label)

        return "[swp_node object]: {} - Matrix:{}, Level:{}, ID:{}{}{}{}{}{}".format(self.type.ljust(11),
                                                                                     self.matrix,
                                                                                     self.level,
                                                                                     self.id,
                                                                                     group,
                                                                                     ch,
                                                                                     label,
                                                                                     user_label,
                                                                                     connected_source)


def get_by_matrix_level(matrix, level, nodes):
    """
    Take a list of Nodes and return Nodes with given matrix & level
    :param matrix: int
    :param level: int
    :param nodes: list of Node objects
    :return: list of Node objects of given matrix & level
    """
    r = []
    for node in nodes:
        if node.matrix == matrix and node.level == level:
            r.append(node)
    return r


def get_consecutive_nodes(nodes, matrix=1, level=1, max_set_size=64):
    """
    Splits a list of nodes into lists of nodes with consecutive IDs for a given matrix & level
    :param nodes: list of Node objects
    :param matrix: int
    :param level: int
    :param max_set_size: int, limit max size of the node lists (max tally qty in a tally dump message is 64)
    :return: list of lists of sorted consecutive nodes
    """
    nodes = get_by_matrix_level(matrix, level, nodes)
    r = []
    l = []
    # Sort node list by their ids (the lambda is equivalent of `def get_id(node): return node.id`
    nodes.sort(key=lambda n: n.id)
    # Split single node list into lists of nodes with consecutive IDs

    for n in range(len(nodes)):
        try:
            # Check if nodes have consecutive ids
            if nodes[n+1].id - nodes[n].id == 1:
                # Check if already added (to add first entry in new list)
                if nodes[n] not in l:
                    l.append(nodes[n])
                # Add the next one
                l.append(nodes[n + 1])

            else:
                l = set_max_list_len(l, max_set_size)
                for i in l:
                    r.append(i)
                l = []
        except IndexError:
            pass

    l = set_max_list_len(l, max_set_size)
    for i in l:
        r.append(i)
    return r


def set_max_list_len(node_list, max_len):
    return [node_list[i * max_len:(i + 1) * max_len] for i in range((len(node_list) + max_len - 1) // max_len)]


def get_connected_sources(destination_list):
    """
    :param destination_list: list of Node.destination objects
    :return: list of connected sources for each destination
    """
    r = []
    for dest in destination_list:
        if dest.connected_source:
            r.append(dest.connected_source.id)
        else:
            r.append(swp_utils.MUTE_ID)
    return r


if __name__ == '__main__':

    cli_utils.print_header(TITLE, VERSION)

    source = Node.source(1, 2, 3, "group label", "channel label", "node label", "user label")
    destination = Node.destination(4, 5, 6, "group label", "channel label", "node label", "user label")

    print(source)
    print(destination)

    # Create unsorted node list
    matrix = 1
    level = 1
    nodes = []
    ids = [100, 1, 2, 99, 50, 4, 98, 101, 5, 7, 6, 49, 51]  # unsorted list of IDs
    for i in ids:
        nodes.append(Node.destination(matrix, level, i))  # list of unsorted nodes
    # Add some more on different matrix/level
    matrix = 2
    level = 2
    for i in ids:
        nodes.append(Node.destination(matrix, level, i))  # list of unsorted nodes

    # Split node list into sorted lists of nodes with consecutive ids in default matrix/level of 1/1
    consecutive_nodes = get_consecutive_nodes(nodes, matrix=2, level=2)

    for node_list in consecutive_nodes:
        print("--------------")
        for node in node_list:
            print(node)

    nodes = []
    for i in range(200):
        nodes.append(Node.destination(1, 1, i))

    consecutive_nodes = get_consecutive_nodes(nodes, matrix=1, level=1)
    for node_list in consecutive_nodes:
        print("--------")
        for node in node_list:
            print(node)
        print(len(node_list))