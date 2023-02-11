# Utility functions for router_emulator.py
# Peter Walker Feb 2023

import cli_utils

TITLE = 'router utils'
VERSION = 0.1


def get_consecutive_nodes(nodes):
    """
    :param nodes: list of Node objects
    :return: list of lists of sorted consecutive nodes
    NOTE: all nodes should be same matrix/level / should have uniques IDs
    (only sorts by ID - this function will not work properly if there is more than one node with the same ID)
    """
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
                r.append(l)
                l = []
        except IndexError:
            pass
    r.append(l)
    return r


if __name__ == '__main__':
    from swp_node import Node
    cli_utils.print_header(TITLE, VERSION)
    matrix = 1
    level = 1
    node_type = 'Destination'
    nodes = []
    ids = [100, 1, 2, 99, 50, 4, 98, 101, 5, 7, 6, 49, 51]
    for i in ids:
        nodes.append(Node(matrix, level, i, node_type))

    consecutive_nodes = get_consecutive_nodes(nodes)
    for node_list in consecutive_nodes:
        print("--------------")
        for node in node_list:
            print(node)
