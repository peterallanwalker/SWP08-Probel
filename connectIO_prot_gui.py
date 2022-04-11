# - Attempt to get a GUI going using pyQt
# - pip3 install PyQt5
# - Peter Walker, April 2022

# - TODO - auto connect / reconnect / handle router coming up after app start and reconnect attempts on loss

import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel

import cli_utils
import connection_settings as config
from connection import Connection

TITLE = "ConnectIO GUI"
VERSION = 0.1

REFRESH_RATE = 100


class Destination:

    def __init__(self, destination, router, parent_window=None):
        """
        :param parent_window:
        :param strip_data: Strip object from CSCP_mixer, usually passed as mixer.strips[i] referencing a CSCP_mixer.Mixer() object
        """
        self.destination_data = router.destinations[destination]

        strip_widget = QWidget()
        strip_widget.setProperty("cssClass", ["strip"])

        strip_layout = QVBoxLayout()
        strip_widget.setLayout(strip_layout)

        strip_label = QLabel(str(self.destination_data.id + 1), alignment=Qt.AlignCenter)
        strip_label.setProperty('cssClass', ["strip"])
        strip_layout.addWidget(strip_label)

        #self.main_routing = Routing(self.strip_data.id, mixer, 'Main', button_qty=4, pages=1)
        #self.aux_routing = Routing(self.strip_data.id, mixer, 'Aux')
        #self.input_routing = InputRouting(self.strip_data.id, mixer)
        #self.display = Display(self.strip_data.id, mixer)
        #self.fader = Fader(self.strip_data.id, mixer)

        #strip_layout.addWidget(self.main_routing.routing_widget)
        #strip_layout.addWidget(self.aux_routing.routing_widget)
        #strip_layout.addWidget(self.input_routing.input_routing_widget)
        #strip_layout.addWidget(self.display.display_widget)
        #strip_layout.addWidget(self.fader.fader_widget)

        parent_window.addWidget(strip_widget)

    def refresh(self):
        pass
        #self.display.refresh()
        #self.input_routing.refresh()
        #self.main_routing.refresh()
        #self.aux_routing.refresh()
        #self.fader.refresh()


class CrossPointView(QWidget):
    def __init__(self, router):
        # - Initialise the QWidget base class that this class is inheriting from
        super().__init__()
        self.router = router

    def refresh(self):
        pass


class Router:
    def __init__(self, settings):
        self.connection = Connection(settings["Router IP Address"], settings["Port"], settings["Protocol"])


    def process_messages(self):
        print("[connectIO_prot_gui.Router.process_messages]: processing messages")
        # TODO!


class RouterGui(QMainWindow):
    """ Main Window.
        Subclass of QMainWindow to setup the GUI
    """
    def __init__(self, router):
        super().__init__()
        self.router = router
        # Set some main window's properties
        self.setWindowTitle(' '.join((TITLE, str(VERSION))))

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
        self.router.process_messages()  # TODO - think about moving this to a thread in mixer
        self.centralWidget().refresh()
        self.update_status()


def main(router, qss):
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
    view = RouterGui(router)
    # Show it
    view.show()
    # Execute the GUI's main loop and handle the exit
    sys.exit(router_app.exec_())


if __name__ == '__main__':

    cli_utils.print_header(TITLE, VERSION)

    qss = 'stylesheet_01.qss'  # External style sheet to use

    # - TODO - move settings config into GUI menu
    # - Get last used settings, and prompt user to accept or change
    # - Note my router is 192.169.1.201
    settings = config.get_settings()
    # - Save user confirmed settings for next time
    config.save_settings(settings)

    router = Router(settings)
    main(router, qss)

