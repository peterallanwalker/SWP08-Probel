# - GUI for SWP08 Router Control
#
# - Using PyQT5, some helpful sites:
# - Ref: https://www.pythonguis.com/tutorials/pyqt-layouts/
# - Ref: https://www.tutorialspoint.com/pyqt/

# highlight source/dest row on hover
# tabs for matrix/levels
# setting for label char len
# settings for connection
# import csv from gui
# create option - link levels to connect ID across levels in same matrix
# (e.g. for stereo/surround route with single x-point switxh
# Test & handle large numbers of IDs - scrollable, collapse by group heading?
# When sending a message, should wait up to 1s for ACK/NAK, If NAK or no ACK after 1s, retry 3 times
# .. report failure if still no ACK, and then continue (do not keep sending messages until all that done)
# ... so instead of widget call-backs directly sending messages to the router, should have a buffer
# ... ... all that can/should be handled by the interface/model, or connection, not here in the GUI.
#
# menu
#
# Load/save salvos
# Add status /connection info, + IO csv name
# - add silence/disconnect source, then maybe play with hover highlighting
# - Stop label edit being focused on load.
# - set a max width on the label edit field.

# - TODO *** v04 is working, now need to deal with large numbers of cross-points so moving to v05
# - TODO - +1 swp values for GUI display labels so they match calrec csv/UI
# - TODO - present different matrices and layers in different tabs using grids in a stacked layout
# -        ... Will be a lot of hardcoded matrix, level = 0, 0  to deal with.
# - TODO - Make the scrollable area just scroll the cross-point grid, but keep source & dest labels withing view...
#          ...put labels in separate grids, somehow link the CP vert scroll to the source label layout
#          & cp horiz scroll to the dest layout, and hide the scroll bars on the label grids

# - TODO apply IP address change to router while running
# - TODO - ** improve status bar connection state text and colour, add connection name to display in
# - TODO - Fix connection fail/retry
# - TODO - Add view menu to select matrix/level (& display current matrix/level within view
# - TODO - instead of scrolling the cross-points, could provide < > buttons and redraw CP grid
#           ... perhaps just hide cols/rows?
# - TODO - fix when changing io data, getting residual labels displayed in background still
# - TODO - load /query connection state on connection. Test with randomly made connections in virtual router

# - TESTING GUI V6 with IMPULSE
# - Editing labels pushes only 4 chars (connection + label pushes 12 char (or at least impulse applies 12 chars
# - connection is being dropped!
# - set fixed width cols & try to prevent alignment to bottom right
# - fix router Ip changes
# - swap out fixed widths for max widths?
# - provide a messaging view
# - get current connections on start
# - handle router IP changes during runtime

import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QScrollArea, QGridLayout, QVBoxLayout, QPushButton, \
    QLabel, QLineEdit, QTextEdit, QDialog, QDialogButtonBox, QFileDialog, QMessageBox, QStatusBar, QAction
from PyQt5.QtGui import QPalette, QColor, QPainter

import cli_utils
import connectIO_gui_settings as config
from swp_router import Router

TITLE = "ConnectIO"
VERSION = 0.6

# - GUI LOOP SPEED IN ms
REFRESH_RATE = 50

# - Background & text colours for state indication (for use in status bar depending on connection state)
STATE_STYLES = {"good": "background-color:#0a0; color:black;",  # - Green
                "warning": "background-color:#FF8C00; color:white;",  # - Amber
                "error": "background-color:#a00; color:white;",  # - Red
                }

# - Styles to use for different connection states
CONNECTION_STATES = {"Starting": STATE_STYLES["warning"],
                     "Connected": STATE_STYLES["good"],
                     "Connection Lost!": STATE_STYLES["error"],
                     "Not Connected": STATE_STYLES["error"]
                     }

# - Row/Col references for positioning within the cross-point grid layout
HEADER_ROW = 0
SOURCE_HEADER_ROW = HEADER_ROW + 3
FIRST_SOURCE_ROW = SOURCE_HEADER_ROW + 1
DEST_HEADER_ROW = HEADER_ROW + 1
DEST_HEADER_COL = 3
FIRST_DEST_COL = DEST_HEADER_COL + 1

FIRST_CP_COL = FIRST_DEST_COL

#COL_WIDTH = 50
CROSS_POINT_WIDTH = 50
#ROW_HEIGHT = 50
EDIT_LABEL_WIDTH = 150
#LABEL_WIDTH = 160
#ID_LABEL_WIDTH = 30
#NUDGE_BUTTON_WIDTH = 100

LABEL_WIDTH = {"id": 20,
               "label": 100,
               "ulabel": 100}

# - NUMBER OF ROWS / COLS TO SKIP WHEN NUDGING GRID
NUDGE_STEP_SIZE = 2


def create_labels(router, matrix, level, io_type, label_type):
    """
    :param router: Router object
    :param matrix: int
    :param level: int
    :param io_type: str "source" or "destination"
    :param label_type: str "id", "label" or "ulabel"
    :return: list of QLabels (for use as cross-point row/col headings)
    """
    r = []

    for node in router.io['matrix'][matrix]['level'][level][io_type].values():
        if io_type == 'destination':
            label = VerticalLabel()
            #label.setFixedHeight(LABEL_WIDTH[label_type]) # THIS IS FORCING THE WIDTH OF THE COLUMN, NOT THE HEIGHT
            label.setFixedWidth(CROSS_POINT_WIDTH)
        else:
            label = QLabel()
            label.setFixedWidth(LABEL_WIDTH[label_type])


        if label_type == 'id':
            label.setText(str(node.id))
            #label.setFixedWidth(30)
        elif label_type == 'label':
            label.setText(str(node.label))
        elif label_type == 'ulabel':
            label.setText(str(node.user_label))
        else:
            print("[connectIO_gui.create_labels]: Unknown label type: {}".format(label_type))
            return False

        r.append(label)
    return r


def create_editable_external_source_labels(router, matrix, level):
    """
    :param router: Router object
    :param matrix: int
    :param level: int
    :return: list of QLineEdits with callbacks to update the router model when edited
    """
    r = []
    for node in router.io['matrix'][matrix]['level'][level]["source"]:
        editable_label = QLineEdit('')
        editable_label.editingFinished.connect(create_source_edit_callback(router, node, editable_label))
        #editable_label.setFixedWidth(EDIT_LABEL_WIDTH)  # - For some reason this limits size but overlaps into next column
        editable_label.setMaximumSize(EDIT_LABEL_WIDTH, 30)

        r.append(editable_label)
    return r


def create_cross_point_buttons2(router, matrix, level):
    destinations = []
    for dest in router.io['matrix'][matrix]['level'][level]["destination"].values():
        sources = []
        for src in router.io['matrix'][matrix]['level'][level]["source"].values():
            btn = QPushButton(str(dest.id) + "-" + str(src.id))  # Label is for debug TODO - REMOVE LABEL ONCE DEBUGGED!
            btn.setCheckable(True)
            btn.setProperty('cssClass', ['cross_point'])
            tooltip = create_cross_point_tooltip(src, dest)
            btn.setToolTip(tooltip)
            btn.clicked.connect(create_cross_point_callback(router, src, dest))
            btn.setFixedWidth(CROSS_POINT_WIDTH)
            sources.append(btn)
        destinations.append(sources)
    return destinations


def create_cross_point_buttons(router, matrix, level):
    destinations = []
    for dest in router.io['matrix'][matrix]['level'][level]["destination"].values():
        sources = []
        for src in router.io['matrix'][matrix]['level'][level]["source"].values():
            btn = CrossPointButton(str(dest.id) + "-" + str(src.id), src.id, dest.id)  # Label is for debug TODO - REMOVE LABEL ONCE DEBUGGED!
            btn.setCheckable(True)
            btn.setProperty('cssClass', ['cross_point'])
            tooltip = create_cross_point_tooltip(src, dest)
            btn.setToolTip(tooltip)
            btn.clicked._connect(create_cross_point_callback(router, src, dest))
            btn.setFixedWidth(CROSS_POINT_WIDTH)
            sources.append(btn)
        destinations.append(sources)
    return destinations


def create_cross_point_grid(source_labels, source_user_labels, source_id_labels, source_external_labels,
                            destination_labels, destination_user_labels, destination_id_labels, cross_point_columns):

    layout = QGridLayout()

    # - Source label column headings
    heading_1 = QLabel('External Source')
    heading_2 = QLabel('Local Source')
    heading_1.setFixedWidth(EDIT_LABEL_WIDTH)
    heading_1.setAlignment(Qt.AlignBottom)
    heading_2.setAlignment(Qt.AlignBottom)
    layout.addWidget(heading_1, SOURCE_HEADER_ROW, 0)
    layout.addWidget(heading_2, SOURCE_HEADER_ROW, 1, 1, 2)  # - this one spans 2 cols (5th arg)

    # - Source label columns
    row = FIRST_SOURCE_ROW
    col = 0
    for label in source_external_labels:
        layout.addWidget(label, row, col)
        row += 1

    row = FIRST_SOURCE_ROW
    col += 1
    for label in source_user_labels:
        layout.addWidget(label, row, col)
        row += 1

    row = FIRST_SOURCE_ROW
    col += 1
    for label in source_labels:
        layout.addWidget(label, row, col)
        row += 1

    row = FIRST_SOURCE_ROW
    col += 1
    for label in source_id_labels:
        layout.addWidget(label, row, col)
        row += 1

    # - Destinations heading
    destination_header = VerticalLabel('Destination')
    destination_header.setFixedWidth(LABEL_WIDTH['id'])
    #destination_header.setFixedHeight(COL_WIDTH-100)
    layout.addWidget(destination_header, DEST_HEADER_ROW, DEST_HEADER_COL, 2, 1)

    # - Destination labels
    row = DEST_HEADER_ROW
    col = FIRST_DEST_COL
    for label in destination_user_labels:
        layout.addWidget(label, row, col)
        col += 1

    row += 1
    col = DEST_HEADER_COL + 1
    for label in destination_labels:
        layout.addWidget(label, row, col)
        col += 1

    row += 1
    col = DEST_HEADER_COL + 1
    for label in destination_id_labels:
        layout.addWidget(label, row, col)
        col += 1

    # - Cross-points
    row = FIRST_SOURCE_ROW
    col = FIRST_CP_COL
    for dest in cross_point_columns:
        for src in dest:
            #src.setFixedWidth(COL_WIDTH)
            layout.addWidget(src, row, col)
            row += 1
        row = FIRST_SOURCE_ROW
        col += 1

    return layout


def position_lr_nudge_buttons(parent):
    parent.nudge_left.setParent(None)
    parent.nudge_right.setParent(None)
    parent.cross_point_grid.addWidget(parent.nudge_left, HEADER_ROW, DEST_HEADER_COL + 1 + parent.scroll_h)
    parent.cross_point_grid.addWidget(parent.nudge_right, HEADER_ROW, DEST_HEADER_COL + 2 + parent.scroll_h)


def refresh_nudge_buttons(parent):

    if parent.scroll_h < NUDGE_STEP_SIZE:
        parent.nudge_left.hide()
    else:
        parent.nudge_left.show()

    if parent.scroll_h >= len(parent.cross_point_columns) - NUDGE_STEP_SIZE:
        parent.nudge_right.hide()
    else:
        parent.nudge_right.show()

    # -

    if parent.scroll_v < NUDGE_STEP_SIZE:
        parent.nudge_up.hide()
    else:
        parent.nudge_up.show()

    if parent.scroll_v >= len(parent.cross_point_columns[0]) - NUDGE_STEP_SIZE:
        parent.nudge_down.hide()
    else:
        parent.nudge_down.show()


# - NEW ABOVE, DEPRECATED BELOW
def create_source_label_edit_col_OLD(router, grid_layout, row=0, col=0):
    """
    Creates text input fields for source labels, and places them into a column of a grid layout
    :param sources: Dict of sources, as supplied by import_io's sources{matrix{level{id{data}}}}
    :param grid_layout: A pyQt QGridLayout
    :param row: int - Grid row for first source label to be displayed (top rows will get used for headers)
    :param col: int - column within QGridLayout to display them in
    :return: dict, keys = ID, values = QLineEdit widgets
    """
    # QLineEdit Widget info: https://www.tutorialspoint.com/pyqt/pyqt_qlineedit_widget.htm

    # - Add column header to the grid
    grid_layout.addWidget(QLabel("External Source Labels"), row, col)
    matrix, level = 0, 0  # TODO!!
    sources = router.io['matrix'][matrix]['level'][level]['source']
    # r = {}
    for src in sources:
        row += 1
        # source_label_edit = QLineEdit(sources[src].user_label)
        source_label_edit = QLineEdit('')
        source_label_edit.editingFinished.connect(create_source_edit_callback(router, src, source_label_edit))
        # source_label_edit.setMaximumWidth(160)
        #source_label_edit.setFixedWidth(160)
        # r[int(src)] = source_label_edit
        # grid_layout.addWidget(r[int(src)], row, col)
        grid_layout.addWidget(source_label_edit, row, col)

    # return r


def create_source_edit_callback(router, source, label):
    """ see create_cross_point_callback docstring for info on why and how this works
        In this case, unlike the cross-points, we need to read the input from the text edit each time
        so are passing the QLineEdit to this function to achieve that
    """
    matrix, level = 0, 0  # TODO!!!

    def source_edit_callback():
        print("[connectIO source edit callback]: Source label edited, source {}, label {}".format(source, label.text()))
        # dest = get_connected_dest(source, router)
        # if dest:
        # router.connection.send(Message.push_labels([label.text()], int(dest)).encoded)
        #    router.update_source_label(source, label.text())
        router.update_source_label(matrix, level, source, label.text())

    return source_edit_callback


def create_source_label_col(sources, grid_layout, label='label', row=2, col=1):
    """
    Create a column of labels and insert into a grid_layout
    :param sources: Dict of sources, as supplied by import_io's sources{matrix{level{id{data}}}}
    :param grid_layout: A pyQt QGridLayout
    :param label: Str - label to use, default='label', or user-label 'ulabel', or 'id'
    :param row: int - Grid row of QGridLayout for heading
    :param col: int - column within QGridLayout to display them in
    :return:
    """
    # heading = get_heading(label)
    # - Add column header to the grid, 3rd & 4th Args specify how many cells within the grid to take up (merges cells)
    # grid_layout.addWidget(QLabel(heading, alignment=Qt.AlignBottom), row, col, 1, 2)

    for src in sources:
        row += 1
        if label == 'id':
            text = QLabel(str(sources[src].id))
        elif label == 'label':
            text = QLabel(sources[src].label)
        elif label == 'ulabel':
            text = QLabel(sources[src].user_label)
        grid_layout.addWidget(text, row, col)


def create_destination_labels(destinations, grid_layout, label='label', row=0, col=2):
    # - Add column header to the grid
    # heading = get_heading(label)
    # grid_layout.addWidget(VerticalLabel(heading), row, col)

    for dst in destinations:
        col += 1
        if label == 'id':
            text = VerticalLabel(str(destinations[dst].id))
        elif label == 'label':
            text = VerticalLabel(destinations[dst].label)
            # text.setAlignment(Qt.AlignCenter)
        elif label == 'ulabel':
            text = VerticalLabel(destinations[dst].user_label)

        grid_layout.addWidget(text, row, col)


def create_cross_point_tooltip(src, dst):
    src_u_label = ''
    dst_u_label = ''
    if src.user_label:
        src_u_label = f' - {src.user_label}'
    if dst.user_label:
        dst_u_label = f' - {dst.user_label}'

    return f'Source ID: {src.id} - {src.label}{src_u_label}\n    --->\nDest:  ID: {dst.id} - {dst.label}{dst_u_label}'


def create_cross_points(router, grid_layout, row=2, col=4):
    """
    Creates a cross-point routing grid
    :param sources: Dict of sources, as supplied by import_io's sources{matrix{level{id{data}}}}
    :param destinations: Dict of destinations, as supplied by import_io's destinations{matrix{level{id{data}}}}
    :param grid_layout: A pyQt QGridLayout
    :param row: int - Grid row for first source label to be displayed (top rows will get used for headers)
    :param col: int - column within QGridLayout to display them in
    :return: dict, keys =  destination ID, values = QPushButton widgets
    """
    destinations = {}
    matrix, level = 0, 0  # TODO
    for dst_id, dst_node in router.io['matrix'][matrix]['level'][level]['destination'].items():
        sources = {}
        curr_row = row
        for src_id, src_node in router.io['matrix'][matrix]['level'][level]['source'].items():
            btn = QPushButton(checkable=True)
            btn.setProperty('cssClass', ['cross_point'])
            tooltip = create_cross_point_tooltip(src_node, dst_node)
            btn.setToolTip(tooltip)
            btn.clicked.connect(create_cross_point_callback(router, src_node, dst_node))
            grid_layout.addWidget(btn, curr_row, col)
            sources[src_node.id] = btn
            curr_row += 1
        destinations[dst_node.id] = sources
        col += 1

    return destinations


def create_cross_point_callback(router, source, destination):
    """
    When creating widgets procedurally, e.g. with a for loop, it seems you cannot connect
    callbacks with iterative vars...
       e.g. pseudo-code: for i, x in list: widget = widget(x).connect(lambda: do_thing(i))
       ... results in every widget having the same value of i, the last value of the loop!
    Instead of assigning the function directly to connect, pass it a function that creates the
    callback, like this one to address this issue.
    ... So, rather than each widget calling the same function with different params, we are actually
    connecting a different function to each widget, each with the params hard-coded within!

    :param router: instance of interface.Router
    :param source:
    :param destination:
    :return: function
    """

    def cross_point_callback():
        print("[connectIO cross-point callback]:CROSSPOINT CLICKED source:{}, dest:{}".format(source, destination))

        router._connect(source, destination)

    return cross_point_callback


def create_cross_point_matrix(parent):
    grid_layout = QGridLayout()

    if parent.router.io:
        grid_layout.addWidget(parent.io_data, 0, 0, 3, 3)  # - Display name of source csv data in top-left.
        grid_layout.addWidget(QLabel("ID"), 3, 1)  # - Source ID column header
        grid_layout.addWidget(VerticalLabel("ID"), 0, 4)  # - Dest ID column header

        # - Apply source label column header, spanning 2 cols (4th arg)
        grid_layout.addWidget(QLabel("Sources"), 3, 2, 1, 2)
        # - Apply destination label row header, spanning 2 rows (3rd arg)
        dest_label_header = VerticalLabel("Destinations")
        # - Don't seem to be able to set alignment on vertical labels here
        # - ... need to look at the paint stuff in the vertical labels class
        # dest_label_header.setAlignment(Qt.AlignLeft)
        grid_layout.addWidget(dest_label_header, 1, 4, 2, 1)
        # grid_layout.addWidget(VerticalLabel("Destinations"), 1, 3, 2, 1)

        matrix, level = 0, 0  # - TODO deal with diff/all matrix/levels with a stacked layout (or relaod for specific matrix/level
        # - Create source label columns
        create_source_label_col(parent.router.io['matrix'][matrix]['level'][level]['source'], grid_layout, label='id',
                                row=3,
                                col=1)
        create_source_label_edit_col(parent.router, grid_layout, row=3, col=0)
        create_source_label_col(parent.router.io['matrix'][matrix]['level'][level]['source'], grid_layout,
                                label='ulabel',
                                row=3, col=2)
        create_source_label_col(parent.router.io['matrix'][matrix]['level'][level]['source'], grid_layout,
                                label='label',
                                row=3, col=3)

        # - Create dest label rows
        create_destination_labels(parent.router.io['matrix'][matrix]['level'][level]['destination'], grid_layout,
                                  label='id',
                                  row=0, col=5)
        create_destination_labels(parent.router.io['matrix'][matrix]['level'][level]['destination'], grid_layout,
                                  label='ulabel', row=1, col=5)
        create_destination_labels(parent.router.io['matrix'][matrix]['level'][level]['destination'], grid_layout,
                                  label='label', row=2, col=5)

        # - Create the cross-point grid
        parent.cross_points = create_cross_points(parent.router, grid_layout, row=4, col=6)

        # scroll = QScrollArea()
        # scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # scroll.setWidgetResizable(True)
        # scroll.setLayout(grid_layout)  # Add the cross-point grid to the scroll area
    return grid_layout


def select_io_file(parent):
    """ Create file-browse menu for selecting a new IO.csv file, load it into the router and replace the cross-point
        matrix to match the new IO
    """

    # - Create file-browse dialogue
    dialog = QFileDialog()
    dialog.setWindowTitle(TITLE + ": Select an I/O data file")
    dialog.setNameFilter("*.csv")

    # - When User selecting a file...
    if dialog.exec():
        filename = dialog.selectedFiles()[0]
        valid = parent.router.load_io_config(filename)

        if valid:
            # - Remove existing cross-point widgets
            # - https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
            for cp in reversed(range(parent.cross_point_grid.count())):
                parent.cross_point_grid.itemAt(cp).widget().setParent(None)

            parent.cross_point_grid.setParent(None)  # Not sure this is needed

            parent.cross_point_grid = create_cross_point_grid(parent.source_labels,
                                                              parent.source_user_labels,
                                                              parent.source_id_labels,
                                                              parent.source_external_labels,
                                                              parent.destination_labels,
                                                              parent.destination_user_labels,
                                                              parent.destination_id_labels,
                                                              parent.cross_point_columns)

            # self.cross_point_grid.setAlignment(Qt.AlignLeft)
            parent.background_layout.addLayout(parent.cross_point_grid, 1, 1)

            # - TODO Resize
            # - TODO, I'm still seeing labels from the previous cp grid!!

            # - Update main window title
            parent.setWindowTitle(TITLE + ", v" + str(VERSION) + " - " + parent.router.source_data)

            # Update IO data source button label
            parent.io_data.setText(Path(router.source_data).stem)

            config.save_settings(parent.router.settings)
            # return filename

        else:
            alert('Failed to import I/O file!',
                  info="Check the csv file headers match Calrec VPB exported file format.")
            # - Present file browse for import again
            select_io_file(parent)
    else:
        return False


def create_select_io_file_callback(parent):
    def select_io_file_callback():
        select_io_file(parent)

    return select_io_file_callback


def create_settings_callback(parent):
    def settings_callback():
        dlg = Settings(parent)

        # - On user clicking OK
        if dlg.exec():
            name = dlg.router_name_field.text()
            ip_address = dlg.ip_address_field.text()
            valid = config.validate_ip_address(ip_address)
            if not valid:
                alert("Please enter a valid IP address (IPv4)")
                settings_callback()  # - Present dialogue again
            else:
                print("Success!", name, ip_address)
                parent.router.settings['Router Name'] = name
                parent.router.settings['Router IP Address'] = ip_address
                config.save_settings(parent.router.settings)
        else:
            print("Cancel!")

    return settings_callback


def alert(text, info='', title=TITLE):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText(text)
    msg.setInformativeText(info)
    msg.setWindowTitle(title)
    # - 'exec' is a python keyword in Python 2, so PyQT4 'uses exec_', with Python3, PyQT supports either exec_ or exec
    msg.exec_()
    # msg.exec()


def refresh_cp_view(parent):
    """
    in lieu of working out how to get scroll bars on the matrix that keep source/dest label headers within view,
    instead using widget.show() & widget.hide() set which rows/columns are being displayed
    :param parent: The GUIs MainWindow
    """
    top_row = parent.scroll_v
    left_col = parent.scroll_h

    destination_labels = (parent.destination_labels, parent.destination_user_labels, parent.destination_id_labels)
    source_labels = (parent.source_external_labels, parent.source_labels, parent.source_user_labels,
                     parent.source_id_labels)

    # - Show/Hide destination labels based on horizontal "scroll" position
    for heading in destination_labels:
        for i, label in enumerate(heading):
            if i >= left_col:
                label.show()
            else:
                label.hide()

    # - Show/Hide source labels based on vertical "scroll" position
    for heading in source_labels:
        for i, label in enumerate(heading):
            if i >= top_row:
                label.show()
            else:
                label.hide()

    # - Show cross-points based on horizontal and vertical view scroll position
    for col, dest in enumerate(parent.cross_point_columns):
        for row, cp in enumerate(dest):
            if row >= top_row and col >= left_col:
                cp.show()
            else:
                cp.hide()


def create_nudge_right_callback(parent):
    def nudge_right_callback():
        parent.scroll_h += NUDGE_STEP_SIZE
        if parent.scroll_h >= len(parent.cross_point_columns):
            parent.scroll_h = len(parent.cross_point_columns)
        refresh_cp_view(parent)
        refresh_nudge_buttons(parent)
        position_lr_nudge_buttons(parent)
    return nudge_right_callback


def create_nudge_left_callback(parent):
    def nudge_left_callback():
        parent.scroll_h -= NUDGE_STEP_SIZE
        if parent.scroll_h <= 0:
            parent.scroll_h = 0
        refresh_cp_view(parent)
        refresh_nudge_buttons(parent)
        position_lr_nudge_buttons(parent)
    return nudge_left_callback


def create_nudge_down_callback(parent):
    def nudge_down_callback():
        parent.scroll_v += NUDGE_STEP_SIZE
        if parent.scroll_v >= len(parent.cross_point_columns[0]):
            parent.scroll_v = len(parent.cross_point_columns[0])
        refresh_cp_view(parent)
        refresh_nudge_buttons(parent)
    return nudge_down_callback


def create_nudge_up_callback(parent):
    def nudge_up_callback():
        parent.scroll_v -= NUDGE_STEP_SIZE
        if parent.scroll_v < 0:
            parent.scroll_v = 0
        refresh_cp_view(parent)
        refresh_nudge_buttons(parent)
    return nudge_up_callback


class Color(QWidget):
    def __init__(self, color):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)


class VerticalLabel(QLabel):
    """
    qt5 does not provide a direct way to rotate a label, this class achieves it.
    ref:
    https://stackoverflow.com/questions/3757246/pyqt-rotate-a-qlabel-so-that-its-positioned-diagonally-instead-of-horizontally
    """

    def __init__(self, *args):
        QLabel.__init__(self, *args)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.translate(0, self.height())
        painter.rotate(-90)
        painter.drawText(0, int(self.width() / 2), self.text())
        painter.end()

    # - Following required to make cell height expand to fit label length
    def minimumSizeHint(self):
        size = QLabel.minimumSizeHint(self)
        # width of cell still not quite fitting height of label, so multiplying by 1.2
        return QSize(int(size.height() * 1.2), size.width())

    def sizeHint(self):
        size = QLabel.sizeHint(self)
        return QSize(size.height(), size.width())


class CrossPointButton(QPushButton):
    def __init__(self, label, source, destination):
        QPushButton.__init__(self, label)
        #super(CrossPointButton, self, label).__init__()
        self.source = source
        self.destination = destination


class Settings(QDialog):
    """
    Dialogue to present and accept change to router IP address and optional name
    https://www.pythonguis.com/tutorials/pyqt-dialogs/
    """

    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle(TITLE + ' Connection Settings')
        self.layout = QVBoxLayout()

        self.router_name_field = QLineEdit(parent.router.settings['Router Name'])
        self.ip_address_field = QLineEdit(parent.router.settings['Router IP Address'])
        self.layout.addWidget(QLabel("Name:"))
        self.layout.addWidget(self.router_name_field)
        self.layout.addWidget(QLabel("IP Address:*"))
        self.layout.addWidget(self.ip_address_field)

        ok_cancel = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(ok_cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)


class MainWindow(QMainWindow):
    def __init__(self, router):
        super(MainWindow, self).__init__()

        self.router = router
        self.setWindowTitle(TITLE + " v" + str(VERSION) + " - " + self.router.source_data)

        self.matrix = 0
        self.level = 0

        # - Lists of QLabels for source row headings
        self.source_labels = create_labels(self.router, self.matrix, self.level, 'source', 'label')
        self.source_user_labels = create_labels(self.router, self.matrix, self.level, 'source', 'ulabel')
        self.source_id_labels = create_labels(self.router, self.matrix, self.level, 'source', 'id')

        # - List of QLineEdits for source row external/connected source labels
        # -  (editing will update the external/connected source label)
        self.source_external_labels = create_editable_external_source_labels(router, self.matrix, self.level)

        # - Lists of QLabels for destination column headings
        self.destination_labels = create_labels(self.router, self.matrix, self.level, 'destination', 'label')
        self.destination_user_labels = create_labels(self.router, self.matrix, self.level, 'destination', 'ulabel')
        self.destination_id_labels = create_labels(self.router, self.matrix, self.level, 'destination', 'id')

        # - list of lists per destination of source cross-point buttons
        self.cross_point_columns = create_cross_point_buttons(self.router, self.matrix, self.level)

        # Base GUI Layout
        self.background_layout = QGridLayout()
        self.background_layout.setAlignment(Qt.AlignLeft)
        self.background_layout.setAlignment(Qt.AlignTop)
        self.cross_point_grid = create_cross_point_grid(self.source_labels,
                                                        self.source_user_labels,
                                                        self.source_id_labels,
                                                        self.source_external_labels,
                                                        self.destination_labels,
                                                        self.destination_user_labels,
                                                        self.destination_id_labels,
                                                        self.cross_point_columns)

        #self.cross_point_grid.setAlignment(Qt.AlignLeft)
        self.background_layout.addLayout(self.cross_point_grid, 1, 1)

        # - Current view "scroll" position
        # - (index of first element being displayed top and left)
        self.scroll_h = 0
        self.scroll_v = 0

        # - Nudge view buttons
        self.nudge_left = QPushButton("<")  # - TODO get arrow icons or unicode
        self.nudge_right = QPushButton(">")
        self.nudge_up = QPushButton("up")
        self.nudge_down = QPushButton("Dwn")

        self.nudge_left.clicked.connect(create_nudge_left_callback(self))
        self.nudge_right.clicked.connect(create_nudge_right_callback(self))
        self.nudge_up.clicked.connect(create_nudge_up_callback(self))
        self.nudge_down.clicked.connect(create_nudge_down_callback(self))

        self.nudge_left.setFixedWidth(CROSS_POINT_WIDTH)
        self.nudge_right.setFixedWidth(CROSS_POINT_WIDTH)
        self.nudge_up.setFixedWidth(CROSS_POINT_WIDTH)
        self.nudge_down.setFixedWidth(CROSS_POINT_WIDTH)

        #self.nudge_right.setAlignment(Qt.AlignBottom)
        #self.nudge_left.setAlignment(Qt.AlignBottom)

        # - Place nudge buttons
        self.cross_point_grid.addWidget(self.nudge_up, SOURCE_HEADER_ROW - 2, 2)
        self.cross_point_grid.addWidget(self.nudge_down, SOURCE_HEADER_ROW - 1, 2)
        position_lr_nudge_buttons(self)
        refresh_nudge_buttons(self)

        # - Load I/O data file button action
        import_io_action = QAction("&Import IO data", self)
        import_io_action.setStatusTip("Import IO from CSV file")
        import_io_action.triggered.connect(create_select_io_file_callback(self))

        # - Connection settings action
        connection_settings_action = QAction("&Settings", self)
        connection_settings_action.setStatusTip("Router connection settings")
        connection_settings_action.triggered.connect(create_settings_callback(self))

        # - Menu
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        file_menu.addAction(import_io_action)
        file_menu.addAction(connection_settings_action)

        # - Add status bars in footer
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # - Button to change IO file
        self.io_data = QPushButton(Path(router.source_data).stem)  # - Path(path\filename.extension) returns filename
        self.io_data.clicked.connect(create_select_io_file_callback(self))
        # - TODO... find where this button is actually being added to the layout, is it part of the grid build?


        # Add the layout for the cross-point grid
        # TODO, create a separate cross-point grid layout for each matrix & level, set them as stacked and work out
        # how to switch between them!

        # TODO Create scrollable grid
        # - Struggling to get this right, had scroll bars in the right place at one point
        # - but the contents were still scaling to fit within and no handles/bars in the scroll"gutters"

        #self.cp_widget = QWidget()
        #self.cp_matrix = create_cross_point_matrix(self)
        #self.background_layout.addLayout(self.cp_matrix, 1, 1)

        if not router.source_data:
            select_io_file(self)

        # - Create a container for the layout and set it as the central widget
        widget = QWidget()
        widget.setLayout(self.background_layout)

        # - the following works but makes the whole gui scrollable, want to only scroll the cp grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        self.setCentralWidget(scroll)

        # Set up a timer to periodically call refresh
        # TODO - test what happens if refresh code takes longer than REFRESH_RATE interval
        self.timer_tick = 0  # for debug - gui refresh loop counter
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(REFRESH_RATE)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start()

    def update_status_orig(self):
        # TODO - FIX TEXT DISPLAYED IN STATUS BAR BUT ALSO FIX CONNECTION TO HANDLE LOSS AND RETRIES
        # print("REFRESH connection status", self.router.connection.status)
        # status_text = str(self.timer_tick) + ' | ' + self.router.connection.status + ' to ' + self.router.connection.address
        # TODO - OPTIMISE - DONT NEED TO PROCESS ALL THIS LOGIC EVERY GUI TICK
        if not self.router.settings['Router IP Address']:
            status_text = str(self.timer_tick) + ' | ' + \
                          'No IP address configured for router connection (Check File>Settings)'

            # - Set status bar colour to red/warning (with white text)
            self.statusBar.setStyleSheet("background-color:#a00; color:white;")

        else:
            status_text = str(self.timer_tick) + ' | ' + self.router.connection.status

            if self.router.connection.status == 'Connection Lost!':
                self.statusBar.setStyleSheet("background-color:#a00; color:white;")

            elif self.router.connection.status == 'Not Connected':
                # self.statusBar.setStyleSheet("background-color:#444; color:#aaa;")
                self.statusBar.setStyleSheet("background-color:#a00; color:white;")

            else:
                # trying to connect
                self.statusBar.setStyleSheet("background-color:#444; color:#aaa;")
                status_text += ' on ' + self.router.connection.address + ' Port ' + str(self.router.connection.port)

        self.statusBar.showMessage(status_text)  # TODO - show connection status and ping?

        # TODO - set heartbeat if connected, on RHS

    def update_status(self):
        self.statusBar.setStyleSheet(CONNECTION_STATES[self.router.connection.status])
        status_text = self.router.connection.status + " to " + self.router.settings["Router Name"] + \
                      " (" + self.router.settings['Router IP Address'] + ")"
        self.statusBar.showMessage(status_text)

    def refresh(self):
        # TODO - this hard coded matrix/level will catch me out when I come to wokring with different ones!!!
        matrix, level = 0, 0
        # Refresh Cross-Point Grid
        for dest in self.cross_point_columns:
            connected_source = router.io['matrix'][matrix]['level'][level]['destination'][dest[0].destination].connected_source
            for cp in dest:
                if cp.source == connected_source:
                    cp.setChecked(True)
                else:
                    cp.setChecked(False)

                if cp.underMouse():
                    # I'm already highlighting the crosspoint button on hover using simple qss
                    # but wanting to highlight the source/dest labels as well (and possibly the button row/col
                    # print("HOVER over source {}, dest {}".format(source, dest))
                    pass
                    # for src in self.cross_points[dest]:
                    #    print("source highlight", src)
                    #    if int(src) < int(source):
                    #        print("highlighting")
                    #        # Cant get this to work...
                    #        self.cross_points[dest][src].setProperty('cssClass', ['highlight'])
                    # - this one does work but I dont want to set checked
                    # self.cross_points[dest][src].setChecked(True)

                    # This kind of works, (not aligned it yet), but puts over top of buttons/widgets
                    # could try reducing opacity but ideally want to place it in the background
                    # ... would also need to remove the widget...
                    # self.grid_layout.addWidget(Color('red'), int(source), int(dest))

        # Refresh Router Data Model
        self.router.process_incoming_messages()
        self.timer_tick += 1
        self.update_status()


def main(router, qss):
    """ main GUI setup & run
    :param router: Instance of interface.Router - data model and comms interfacce
    :param qss: filename - StyleSheet (CSS-like)
    """
    # Create an instance of QApplication
    app = QApplication(sys.argv)

    # Load qss style sheet
    try:
        with open(qss, "r") as fh:
            app.setStyleSheet(fh.read())
    except FileNotFoundError:
        print("** stylesheet not found **. Expecting a file named {} in the same folder as this file)".format(qss))

    # Create the main window, passing it the router data/comms model.
    window = MainWindow(router)
    window.show()

    # Execute the GUI's main loop,
    # https://stackoverflow.com/questions/45508090/what-is-the-necessity-of-sys-exitapp-exec-in-pyqt
    sys.exit(app.exec_())


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)

    # - External css-like style-sheet
    qss = 'stylesheet_02.qss'
    #qss = 'none'  # - For debugging

    # - Get last used settings
    # - Note my router is 192.169.1.201
    # - Use 127.0.0.1 to connect with virtual router running on same machine for testing / running this GUI offline
    settings = config.load_settings()
    print("[ConnectIO_gui.main]: Settings:\n", settings)

    # Create interface with router
    router = Router(settings)

    # Run the app
    main(router, qss)
