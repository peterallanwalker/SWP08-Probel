# - Ref: https://www.pythonguis.com/tutorials/pyqt-layouts/
# - Ref: https://www.tutorialspoint.com/pyqt/
# TODO - refresh crosspoints
# connect source label edits
# highlight source/dest row on hover
# formatting & css
# link levels
# tabs for matrix/levels
# setting for label char len

# TODO - should push labels on connect, not just on edit of source
# ... or have user option to enable that!
# TODO - getting fed up with issues around IDs being strings not ints
# ... also should should used named matrix/level in data structure, group by matrix leve
# create tab for matrix view
# create tab for lavel
# create option - link levels to connect ID across levels in same matrix
# (e.g. for stereo/surround route with single x-point switxh
# Test & handle large numbers of IDs - scrollable, collapse by group heading?
# user option for char len
# user options in GUI for connection, loading of CSV etc.
# When sending a message, should wait up to 1s for ACK/NAK, If NAK or no ACK after 1s, retry 3 times
# .. report failure if still no ACK, and then continue (do not keep sending messages until all that done)
# ... so instead of widget call-backs directly sending messages to the router, should have a buffer
# ... ... all that can/should be handled by the interface/model, or connection, not here in the GUI.
# I.E. GUI widgets should call handling methods in the model rather than directly call Connection.send!
#
# - styling, css, fix padding, etc
# menu
#
# Load/save salvos
# Add status /connection info, + IO csv name

# TODO ***** this v3 is a good working way point, needs testing with a real router
# Archiving off and starting v04 to add the above features without breaking this version

# - add silence/disconnect source, then maybe play with hover highlighting
# - Stop label edit being focused on load.
# - set a max width on the label edit field.

import sys

from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QPushButton, \
     QLabel, QLineEdit
from PyQt5.QtGui import QPalette, QColor, QPainter

import cli_utils
import connection_settings as config
from import_io import import_io_from_csv
from archive.router import Router

TITLE = "ConnectIO"
VERSION = 0.4

# - GUI LOOP SPEED IN ms
REFRESH_RATE = 10


def get_connected_dest(source, router):
    """
    TODO DEPRECATED, REMOVE - MOVED TO INTERFACE.. NOT SURE IF I STILL HAVE A RELIANCE ON THIS HERE..
    TODO - should take full source data and return full dest data rather than just the IDs in order to be able
    to work with different Matrix/Level values... but there are quite a few areas that need to change to support
    that.
    :param source:
    :param router: instance of interface.Router
    :return: id of the source's first found connected destination
              TODO should really return a list of all connected destinations,
              but Calrec router will update labels on all dests connected from same source
              from a label pushed to a single dest, so only need to know one of them
              so only need to know one of them... for Calrec implementation at least
    """
    #print("[get_connected_dest] source", type(source), source)
    for dest in router.io['destinations']['1']['1']:
        #print("dest ", dest, "connected source", router.io['destinations']['1']['1'][dest]['connected source'])
        if router.io['destinations']['1']['1'][dest]['connected source'] == source:
            #print("[get_connected_dest]: Source {}, first connected dest: {}".format(source, dest))
            return dest


def get_heading(label):
    """ Deprecated as I'm now using a single generic heading spanning the default and user label cols/rows """
    if label == 'label':
        return 'Default Label'
    elif label == 'ulabel':
        return 'User Label'
    else:
        return 'UNDEFINED'


def create_source_label_edit_col(router, grid_layout, row=0, col=0):
    """
    Creates text input fields for source labels, and places them into a column of a grid layout
    :param sources: Dict of sources, as supplied by import_io's sources{matrix{level{id{data}}}}
    :param grid_layout: A pyQt QGridLayout
    :param row: int - Grid row for first source label to be displayed (top rows will get used for headers)
    :param col: int - column within QGridLayout to display them in
    :return: dict, keys = ID, values = QLineEdit widgets
    """
    # QLineEdit Widget info: https: // www.tutorialspoint.com / pyqt / pyqt_qlineedit_widget.htm

    # - Add column header to the grid
    grid_layout.addWidget(QLabel("Connected Sources"), row, col)

    sources = router.io['sources']['1']['1']
    #r = {}
    for src in sources:
        row += 1
        source_label_edit = QLineEdit(sources[src]['ulabel'])
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

    def source_edit_callback():
        print("[connectIO source edit callback]: Source label edited, source {}, label {}".format(source, label.text()))
        dest = get_connected_dest(source, router)
        if dest:
            #router.connection.send(Message.push_labels([label.text()], int(dest)).encoded)
            router.update_source_label(source, label.text())

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
            text = QLabel(src)
        else:
            text = QLabel(sources[src][label])

        grid_layout.addWidget(text, row, col)


def create_destination_labels(destinations, grid_layout, label='label', row=0, col=2):

    # - Add column header to the grid
    #heading = get_heading(label)
    #grid_layout.addWidget(VerticalLabel(heading), row, col)

    for dst in destinations:
        col += 1
        if label == 'id':
            text = VerticalLabel(dst)
        else:
            text = VerticalLabel(destinations[dst][label])
            #text.setAlignment(Qt.AlignCenter)

        grid_layout.addWidget(text, row, col)


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

    for dst in router.io['destinations']['1']['1']:
        sources = {}
        curr_row = row
        for src in router.io['sources']['1']['1']:
            btn = QPushButton(checkable=True)
            #btn.setMaximumWidth(btn.height())  # - doesn't work
            #btn.setProperty('cssClass', ['red'])
            btn.setProperty('cssClass', ['cross_point'])
            # - Cannot directly connect a call-back, all buttons will get set to use the same/last src/dst values
            #btn.clicked.connect(lambda: print("CONNECT- source: {}, dest: {}".format(sources[src], dst)))
            # - Instead, create the call-back separately... not sure why this works but the above does not!
            # - See comment in the create_cross_point_callback function for more info
            btn.clicked.connect(create_cross_point_callback(router, src, dst))
            grid_layout.addWidget(btn, curr_row, col)
            sources[src] = btn
            curr_row += 1
        destinations[dst] = sources
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
        #router.connection.send(Message.connect(int(source), int(destination)).encoded)
        # TODO, pass connected source label
        router.make_connection(int(source), int(destination), matrix=0, level=0)

    return cross_point_callback


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

        # Base GUI Layout
        background_layout = QGridLayout()
        grid_layout = QGridLayout()
        self.grid_layout = grid_layout
        top_left = Color('red')
        top_right = Color('green')
        destination_header = QLabel('Destinations', alignment=Qt.AlignCenter)
        #destination_header.setAlignment(Qt.AlignCenter)
        source_header = QLabel('Sources')
        bottom_left = Color('yellow')

        background_layout.addWidget(top_left, 0, 0)

        background_layout.addWidget(top_right, 0, 1)
        background_layout.addWidget(destination_header, 0, 1)

        background_layout.addWidget(bottom_left, 1, 0)
        background_layout.addWidget(source_header, 1, 0)

        # Add the layout for the cross-point grid
        background_layout.addLayout(grid_layout, 1, 1)

        grid_layout.addWidget(QLabel("ID"), 3, 1)
        grid_layout.addWidget(VerticalLabel("ID"), 0, 4)

        # - Apply source label column header, spanning 2 cols (4th arg)
        grid_layout.addWidget(QLabel("Sources"), 3, 2, 1, 2)
        # - Apply destination label row header, spanning 2 rows (3rd arg)
        dest_label_header = VerticalLabel("Destinations")
        # - Don't seem to be able to set alignment on vertical labels here
        # - ... need to look at the paint stuff in the vertical labels class
        #dest_label_header.setAlignment(Qt.AlignLeft)
        grid_layout.addWidget(dest_label_header, 1, 4, 2, 1)
        #grid_layout.addWidget(VerticalLabel("Destinations"), 1, 3, 2, 1)

        # - Create source label columns
        create_source_label_col(self.router.io['sources']['1']['1'], grid_layout, label='id', row=3, col=1)
        create_source_label_edit_col(self.router, grid_layout, row=3, col=0)
        create_source_label_col(self.router.io['sources']['1']['1'], grid_layout, label='ulabel', row=3, col=2)
        create_source_label_col(self.router.io['sources']['1']['1'], grid_layout, label='label', row=3, col=3)

        # - Create dest label rows
        create_destination_labels(self.router.io['destinations']['1']['1'], grid_layout, label='id', row=0, col=5)
        create_destination_labels(self.router.io['destinations']['1']['1'], grid_layout, label='ulabel', row=1, col=5)
        create_destination_labels(self.router.io['destinations']['1']['1'], grid_layout, label='label', row=2, col=5)

        # - Create the cross-point grid
        self.cross_points = create_cross_points(self.router, grid_layout, row=4, col=6)

        # - Create a container for the layout and set it as the central widget
        widget = QWidget()
        widget.setLayout(background_layout)
        self.setCentralWidget(widget)

        # Set up a timer to periodically call refresh
        # TODO - test what happens if refresh code takes longer than REFRESH_RATE interval
        self.timer_tick = 0  # for debug - gui refresh loop counter
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(REFRESH_RATE)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start()

    def refresh(self):

        # Refresh Cross-Point Grid
        for dest, sources in self.cross_points.items():
            connected_source = router.io['destinations']['1']['1'][dest]['connected source']
            #print("Dest", dest, " connected source: ", connected_source)
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
    # qss = 'none'

    # - TODO - add this to settings/save  / add to GUI
    io_csv = 'VirtualPatchbays.csv'
    io = import_io_from_csv(io_csv)

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
