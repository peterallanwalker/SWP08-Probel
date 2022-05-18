# - Attempt to get a GUI going using pyQt
# - pip3 install PyQt5
# - Peter Walker, April 2022

# - TODO - auto connect / reconnect / handle router coming up after app start and reconnect attempts on loss
# - settings for e.g. push labels
# - display full source dest details on hover
# - display user label in place of default if exists
# - user input for source label pushing
# - interogtae cross points on startup to set display to match router
# - Mute/disconnect source
# - presets/salvos


import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QTextEdit

import cli_utils
import connectIO_cli_settings as config
from archive.connection import Connection
from swp_message import Message  # - TODO not sure I should have this in here, or send direct to router, move the router model into seperate file like mixer was
from import_io import import_io_from_csv

TITLE = "ConnectIO GUI"
VERSION = 0.1

REFRESH_RATE = 100


class DestinationCol:
    """
        A column within the cross-point routing matrix representing an individual destination
        with a cross-point button for each source
    """

    def __init__(self, router, group, channel, label, id, sources, parent_window=None):
        """
        :param parent_window:
        :param strip_data: Strip object from CSCP_mixer, usually passed as mixer.strips[i] referencing a CSCP_mixer.Mixer() object
        """

        #self.destination_data = router.destinations[destination]
        self.router = router
        self.group = group
        self.channel = channel
        self.label = label
        self.id = id
        self.sources = sources

        strip_widget = QWidget()
        strip_widget.setProperty("cssClass", ["strip"])

        strip_layout = QVBoxLayout()
        strip_widget.setLayout(strip_layout)

        #strip_label = QLabel(str(self.destination_data.id + 1), alignment=Qt.AlignCenter)
        strip_label1 = QLabel(self.group, alignment=Qt.AlignCenter)
        strip_label2 = QLabel(self.channel, alignment=Qt.AlignCenter)
        #strip_label.setProperty('cssClass', ["strip"])
        strip_layout.addWidget(strip_label1)
        strip_layout.addWidget(strip_label2)

        #self.btn = QPushButton('PFL', checkable=True)
        #strip_layout.addWidget(self.btn)

        self.cross_points = {}
        for source in self.sources:
            #btn = QPushButton('{}-{}'.format(source['group'], source['channel']), checkable=True)
            #btn = QPushButton(source['id'], checkable=True)
            btn = QPushButton(source['id'], checkable=True)
            #btn = QPushButton(source['id'], checkable=True)

            # Quick and dirty test, should probably send info to router to then pack and send over connection.
            #btn.clicked.connect(router.connection.send(Message.connect(int(source['id']), int(self.id))))
            #btn.clicked.connect(send_connect(source['id'], self.id))
            #btn.clicked.connect(print("CLICKED"))
            btn.clicked.connect(self.create_cross_point_callback(source['id'], self.id))

            # - add the source ID as a new key and set the button as the value
            self.cross_points[source['id']] = btn
            strip_layout.addWidget(btn)

        #print("DESINTATIONS STRIPS, SOURCE BUTTONS:", self.cross_points)

        parent_window.addWidget(strip_widget)

    def create_cross_point_callback(self, source, destination):
        # Quick n dirty to get this working, but should probably hand the actual message pack/send off to the router
        def cross_point_callback():
            print("CROSSPOINT", source, destination)
            self.router.connection.send(Message.connect(int(source), int(destination)).encoded)
        return cross_point_callback

    def refresh(self):
        #print("DEBUG STRIP: DESTINNATION:", self.router.destinations[self.id]['connected source'])
        #print("DEBUG SOURCE BUTTONS", self.cross_points)
        #print("DEBUG REFRESH STRIP")

        # - Set all buttons to unchecked
        for btn in self.cross_points:
            self.cross_points[btn].setChecked(False)
        #    self.cross_points[btn].setProperty('cssClass', ['red'])

        # Look up the connected source for this destination
        connected_source = self.router.destinations[str(self.id)]['connected source']
        if connected_source:
            # - If there is a connected source, mark the appropriate source button as checked
            self.cross_points[str(connected_source)].setChecked(True)
            self.cross_points[str(connected_source)].setProperty('cssClass', ['red'])  # - css not working??

        #for cross_point in self.cross_points:
        #    #print("DEBUG", cross_point)
        #    if self.router.destinations[self.id]['connected source'] == str(cross_point):
        #        print("CONNECTION")
        #        self.cross_points[cross_point].setChecked()

        #f.display.refresh()
        #self.input_routing.refresh()
        #self.main_routing.refresh()
        #self.aux_routing.refresh()
        #self.fader.refresh()


class SourceLabelCol:
    """
    Column of source labels to show down left hand side of the cross-point grid.
    """
    def __init__(self, sources, parent_window=None):
        #self.sources = sources

        strip_widget = QWidget()
        strip_widget.setProperty("cssClass", ["strip"])

        strip_layout = QVBoxLayout()
        strip_widget.setLayout(strip_layout)

        spacer = QLabel("", alignment=Qt.AlignCenter)
        strip_layout.addWidget(spacer)

        for source in sources:
            label = source['group'] + ' - ' + source['channel']
            source_label = QLabel(label, alignment=Qt.AlignCenter)
            strip_layout.addWidget(source_label)

        parent_window.addWidget(strip_widget)


class SourceLabelEditCol:

    def __init__(self, sources, parent_window=None):
        strip_widget = QWidget()
        strip_widget.setProperty("cssClass", ["strip"])

        strip_layout = QVBoxLayout()
        strip_widget.setLayout(strip_layout)

        spacer = QLabel("", alignment=Qt.AlignCenter)
        strip_layout.addWidget(spacer)
        label_edits = {}
        for source in sources:
            label = source['group'] + ' - ' + source['channel']
            source_label = QTextEdit("test")
            #source_label = QLabel(label, alignment=Qt.AlignCenter)
            strip_layout.addWidget(source_label)

        parent_window.addWidget(strip_widget)


class CrossPointView(QWidget):
    def __init__(self, router):
        # - Initialise the QWidget base class that this class is inheriting from
        super().__init__()

        self.router = router
        self.strips_area = QHBoxLayout()
        self.setLayout(self.strips_area)  # - Important else will not display!
        self.sources_edit = SourceLabelEditCol(self.router.sources, parent_window=self.strips_area)
        self.sources = SourceLabelCol(self.router.sources, parent_window=self.strips_area)

        self.destinations = []
        for destination in self.router.destinations:
            self.destinations.append(DestinationCol(router,
                                                    self.router.destinations[destination]['group'],
                                                    self.router.destinations[destination]['channel'],
                                                    self.router.destinations[destination]['label'],
                                                    self.router.destinations[destination]['id'],
                                                    self.router.sources,
                                                    parent_window=self.strips_area
                                                    ))

    def refresh(self):
        for destination in self.destinations:
            destination.refresh()


class Router:
    def __init__(self, settings, sources, destinations):
        self.connection = Connection(settings["Router IP Address"], settings["Port"], settings["Protocol"])
        self.sources = sources

        self.destinations = {}
        # - convert list of dicts to dict of dicts with keys being dest ID
        for destination in destinations:
            self.destinations[destination['id']] = destination

        #self.destinations = destinations

        # Set up connection state for each dest... TODO - readback actual state on startup
        for dest in destinations:
            dest["connected source"] = False  # TODO - use digital silence,

    def process_incoming_messages(self):
        """ Process any messages received on the connection
            CALL THIS PERIODICALLY, PROB FROM GUI LOOP, or maybe put a thread here.
            ... or limit max  time
        """

        while self.connection.receive_buffer_len():

            print("[connectIO_prot_gui.process_incoming messages]: Messages in receive buffer:",
                  self.connection.receive_buffer_len())

            msg = Message.decode(self.connection.get_message())

            # TODO - push ACK NAK back to sender & have them wait/retry
            if msg.command == 'ACK':
                print("[connectIO_prot_gui.process_incoming messages]: >>> ACK received")
            elif msg.command == "NAK":
                print("[connectIO_prot_gui.process_incoming messages]: >>> ** NAK ** received!")
            else:
                msg.print_summary("[connectIO_prot_gui.process_incoming messages]: >>> Received Message:")
                # print("Message received "
                #      "from router:", response)
                self.update_data(msg)

    def update_data(self, message):
        # TODO - parse connect differently / controller should not receieve it but its all my virtual router outputs at mo
        if message.command in ('connected', 'connect'):
            print("[connectIO_prot_gui.update_data]: connect/connected recieved, destinatio:", message.destination)
            # - TODO - optimise data so I dont have to loop to find the right ID, and error check against duplicate IDs,
            # - (on other matrix/level as well as erroneous)

            self.destinations[str(message.destination)]["connected source"] = message.source
            print("updated data", self.destinations[str(message.destination)])

            #for d in self.destinations:
            #    print(d)
            #    if int(d['id']) == message.destination:
            #        d['connected source'] = message.destination
            #        print("UPDATE DATA,", d)







def get_received_messages(conn):

    while len(connection._messages):
        message = conn.get_message()
        #print("Message Recieved", Message.decode(message))
        print("Message Received:", message)






class RouterGui(QMainWindow):
    """ Main Window.
        Subclass of QMainWindow to setup the GUI
    """
    def __init__(self, router, io_mapping_filename):
        super().__init__()
        self.router = router
        # Set some main window's properties
        self.setWindowTitle(TITLE + ", v" + str(VERSION) + "       [" + io_mapping_filename + "]")

        main_view = CrossPointView(self.router)

        self.setCentralWidget(main_view)

        #self.addToolBar(ViewMenu(self))

        # Set up timer to periodically call my refresh code
        self.timerval = 0  # debug - timer loop counter
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(REFRESH_RATE)
        self.refresh_timer.timeout.connect(self.refresh_gui)
        self.refresh_timer.start()

    def update_status(self):
        status_text = str(self.timerval) + ' | ' + self.router.connection.status + ' to ' + self.router.connection.address

        if self.router.connection.status == 'Connection Lost!':
            self.statusBar().setStyleSheet("background-color:#a00; color:white;")

        elif self.router.connection.status == 'Not Connected':
            self.statusBar().setStyleSheet("background-color:#444; color:#aaa;")

        else:
            # trying to connect
            self.statusBar().setStyleSheet("background-color:#444; color:#aaa;")
            status_text += ' on ' + self.router.connection.address + ' Port ' + str(self.router.connection.port)

        self.statusBar().showMessage(status_text)  # TODO - show connection status and ping?

        # TODO - set heartbeat if connected, on RHS

    def refresh_gui(self):
        self.timerval += 1
        self.router.process_incoming_messages()  # TODO - think about moving this to a thread in mixer
        self.centralWidget().refresh()
        self.update_status()


def main(router, qss, io_csv_mapping_filename):
    # Create an instance of QApplication
    router_app = QApplication(sys.argv)

    # Load qss style sheet
    try:
        with open(qss, "r") as fh:
            router_app.setStyleSheet(fh.read())
    except FileNotFoundError:
        print(
            "I'm naked! (stylesheet not found. Expecting a file named {} in the same folder as this file)".format(qss))

    # Create a QMainWindow for the router
    view = RouterGui(router, io_csv_mapping_filename.strip(".csv"))
    # Show it
    view.show()
    # Execute the GUI's main loop and handle the exit
    sys.exit(router_app.exec_())


if __name__ == '__main__':

    cli_utils.print_header(TITLE, VERSION)

    qss = 'stylesheet_01.qss'  # External style sheet to use
    #qss = 'none'

    # - TODO - move settings config into GUI menu
    # - Get last used settings, and prompt user to accept or change
    # - Note my router is 192.169.1.201
    settings = config.get_settings()
    # - Save user confirmed settings for next time
    config.save_settings(settings)

    # - TODO - add this to settings/save  / add to GUI
    io_csv = 'VirtualPatchbays.csv'
    source_list, destination_list = import_io_from_csv(io_csv)

    router = Router(settings, source_list, destination_list)
    main(router, qss, io_csv)

