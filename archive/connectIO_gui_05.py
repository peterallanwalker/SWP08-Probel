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
# - TODO - Use scrollable layout - got working but struggling to get it to just scroll the cp grid
#          (and to keep src/dst labels in view)


import sys

from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QScrollArea, QGridLayout, QVBoxLayout, QPushButton, \
     QLabel, QLineEdit, QTextEdit, QDialog, QDialogButtonBox, QFileDialog
from PyQt5.QtGui import QPalette, QColor, QPainter


import cli_utils
import connectIO_cli_settings as config
from import_io import import_io_from_csv
from swp_router import Router

TITLE = "ConnectIO"
VERSION = 0.5

# - GUI LOOP SPEED IN ms
REFRESH_RATE = 10


def create_source_label_edit_col(router, grid_layout, row=0, col=0):
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
    grid_layout.addWidget(QLabel("Connected Sources"), row, col)
    matrix, level = 0, 0  # TODO!!
    sources = router.io['matrix'][matrix]['level'][level]['source']
    #r = {}
    for src in sources:
        row += 1
        #source_label_edit = QLineEdit(sources[src].user_label)
        source_label_edit = QLineEdit('')
        source_label_edit.editingFinished.connect(create_source_edit_callback(router, src, source_label_edit))
        #r[int(src)] = source_label_edit
        #grid_layout.addWidget(r[int(src)], row, col)
        grid_layout.addWidget(source_label_edit, row, col)

    #return r


def create_source_edit_callback(router, source, label):
    """ see create_cross_point_callback docstring for info on why and how this works
        In this case, unlike the cross-points, we need to read the input from the text edit each time
        so are passing the QLineEdit to this function to achieve that
    """
    matrix, level = 0, 0  # TODO!!!
    def source_edit_callback():
        print("[connectIO source edit callback]: Source label edited, source {}, label {}".format(source, label.text()))
        #dest = get_connected_dest(source, router)
        #if dest:
            #router.connection.send(Message.push_labels([label.text()], int(dest)).encoded)
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
    #heading = get_heading(label)
    # - Add column header to the grid, 3rd & 4th Args specify how many cells within the grid to take up (merges cells)
    #grid_layout.addWidget(QLabel(heading, alignment=Qt.AlignBottom), row, col, 1, 2)

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
    #heading = get_heading(label)
    #grid_layout.addWidget(VerticalLabel(heading), row, col)

    for dst in destinations:
        col += 1
        if label == 'id':
            text = VerticalLabel(str(destinations[dst].id))
        elif label == 'label':
            text = VerticalLabel(destinations[dst].label)
            #text.setAlignment(Qt.AlignCenter)
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
    #parent.cross_point_matrix = parent.background_layout.addLayout(grid_layout, 1, 1)

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
    create_source_label_col(parent.router.io['matrix'][matrix]['level'][level]['source'], grid_layout, label='id', row=3,
                            col=1)
    create_source_label_edit_col(parent.router, grid_layout, row=3, col=0)
    create_source_label_col(parent.router.io['matrix'][matrix]['level'][level]['source'], grid_layout, label='ulabel',
                            row=3, col=2)
    create_source_label_col(parent.router.io['matrix'][matrix]['level'][level]['source'], grid_layout, label='label',
                            row=3, col=3)

    # - Create dest label rows
    create_destination_labels(parent.router.io['matrix'][matrix]['level'][level]['destination'], grid_layout, label='id',
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
    dialog = QFileDialog()
    dialog.setWindowTitle("Select an I/O data file")
    dialog.setNameFilter("*.csv")
    if dialog.exec():
        filename = dialog.selectedFiles()[0]
        parent.router.load_io_config(filename)
        #print("DEBUG CONFIG CHANGE", parent.router.io)
        print("DEBUG CONFIG", parent.cross_points)
        window = MainWindow(parent.router)
        parent.close()
        window.show()

        #main(parent.router, qss)

        #parent.cp_widget.close()

        #parent.background_layout.removeWidget(parent.cp_widget)  # TODO - THIS DOESNT SEEM TO WORK
        #cp_widget = QWidget()
        #cp_matrix = create_cross_point_matrix(parent)
        #cp_widget.setLayout(cp_matrix)
        #parent.background_layout.addWidget(cp_widget, 1, 1)
        # - Create a container for the layout and set it as the central widget
        #widget = QWidget()
        #widget.setLayout(parent.background_layout)

        #cp_widget = QWidget()
        #cp_matrix = create_cross_point_matrix(parent)

        #widget = QWidget()
        #widget.setLayout(cp_matrix)
        #parent.background_layout.addWidget(widget, 1, 1)

        return filename
    else:
        return False


def create_select_io_file_callback(parent):
    def select_io_file_callback():
        select_io_file(parent)
    return select_io_file_callback


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
        painter.drawText(0, int(self.width()/2), self.text())
        painter.end()

    # - Following required to make cell height expand to fit label length
    def minimumSizeHint(self):
        size = QLabel.minimumSizeHint(self)
        # width of cell still not quite fitting height of label, so multiplying by 1.2
        return QSize(int(size.height() * 1.2), size.width())

    def sizeHint(self):
        size = QLabel.sizeHint(self)
        return QSize(size.height(), size.width())


class MainWindow(QMainWindow):
    def __init__(self, router):
        super(MainWindow, self).__init__()

        self.setWindowTitle(TITLE + ", v" + str(VERSION))
        self.router = router

        #self.io_data = QLabel(router.source_data.strip('.csv'), alignment=Qt.AlignCenter)  # - imported IO csv filename
        self.io_data = QPushButton(router.source_data.strip('.csv'))  # - imported IO csv filename
        #self.io_data.clicked.connect(select_io_file)
        self.io_data.clicked.connect(create_select_io_file_callback(self))

        # Base GUI Layout
        self.background_layout = QGridLayout()

        # Add the layout for the cross-point grid
        # TODO, create a separate cross-point grid layout for each matrix & level, set them as stacked and work out
        # how to switch between them!

        # TODO Create scrollable grid
        # - Struggling to get this right, had scroll bars in the right place at one point
        # - but the contents were still scaling to fit within and no handles/bars in the scroll"gutters"
        #scroll_widget = QWidget()
        #scroll = QScrollArea()
        #scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        #scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        #scroll.setWidgetResizable(True)
        #scroll.setWidget(scroll_widget)
        self.cp_widget = QWidget()
        self.cp_matrix = create_cross_point_matrix(self)

        #self.cp_widget.setLayout(self.cp_matrix)
        #self.background_layout.addWidget(self.cp_widget, 1, 1)
        self.background_layout.addLayout(self.cp_matrix, 1, 1)

        # - Create a container for the layout and set it as the central widget
        widget = QWidget()
        widget.setLayout(self.background_layout)

        # - the following works but makes the whole gui scrollable, want to only scroll the cp grid
        scroll = QScrollArea()
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        self.setCentralWidget(scroll)
        #self.setCentralWidget(widget)


        # Set up a timer to periodically call refresh
        # TODO - test what happens if refresh code takes longer than REFRESH_RATE interval
        self.timer_tick = 0  # for debug - gui refresh loop counter
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(REFRESH_RATE)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start()

    def refresh(self):
        # TODO - this hard coded matrix/level will catch me out when I come to wokring with different ones!!!
        matrix, level = 0, 0
        # Refresh Cross-Point Grid
        for dest, sources in self.cross_points.items():
            #connected_source = router.io['destinations']['1']['1'][dest]['connected source']
            connected_source = router.io['matrix'][matrix]['level'][level]['destination'][dest].connected_source
            for source, btn in sources.items():
                if source == connected_source:
                    self.cross_points[dest][source].setChecked(True)
                else:
                    self.cross_points[dest][source].setChecked(False)

                if btn.underMouse():
                    # I'm already highlighting the crosspoint button on hover using simple qss
                    # but wanting to highlight the source/dest labels as well (and possibly the button row/col
                    #print("HOVER over source {}, dest {}".format(source, dest))
                    pass
                    #for src in self.cross_points[dest]:
                    #    print("source highlight", src)
                    #    if int(src) < int(source):
                    #        print("highlighting")
                    #        # Cant get this to work...
                    #        self.cross_points[dest][src].setProperty('cssClass', ['highlight'])
                            # - this one does work but I dont want to set checked
                            #self.cross_points[dest][src].setChecked(True)

                    # This kind of works, (not aligned it yet), but puts over top of buttons/widgets
                    # could try reducing opacity but ideally want to place it in the background
                    # ... would also need to remove the widget...
                    #self.grid_layout.addWidget(Color('red'), int(source), int(dest))

        # Refresh Router Data Model
        self.router.process_incoming_messages()


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
    #qss = 'none'

    # - TODO - add this to settings/save  / add to GUI
    io = 'VirtualPatchbaysb.csv'
    #io = import_io_from_csv(io_csv)

    # - TODO - move settings config into GUI menu
    # - Get last used settings, and prompt user to accept or change
    # - Note my router is 192.169.1.201
    settings = config.get_settings()
    # - Save user confirmed settings for next time
    config.save_settings(settings)

    # Create interface with router
    router = Router(settings, io)

    # Run the app
    main(router, qss)
