# - Ref: https://www.pythonguis.com/tutorials/pyqt-layouts/

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QPushButton, \
     QLabel, QLineEdit
from PyQt5.QtGui import QPalette, QColor

from archive.import_io_2 import import_io_from_csv


def create_source_label_edit_col(sources, grid_layout, start_row=1, col=0):
    """
    Creates text input fields for source labels,
    and places them into a column of a grid layout
    :param sources: Dict of sources, as supplied by import_io
    :param grid_layout: A pyQt QGridLayout
    :param start_row: int - Grid row for first source label to be displayed (top rows will get used for headers)
    :param col: int - column within QGridLayout to display them in
    :return: dict, keys = ID, values = QLineEdit widgets
    """
    r = {}
    for i, src in enumerate(sources):
        r['EDIT Out SW-P-08 ID'] = QLineEdit(str(i) + sources[src]['Virtual Patchbay Name'] + '-' + sources[src]['Patch Point Number'])
        grid_layout.addWidget(r['EDIT Out SW-P-08 ID'], start_row + i, col)

    return r


def create_source_label_col(sources, table_layout, start_row=1, col=1):
    r = {}
    for i, src in enumerate(sources):
        r['EDIT Out SW-P-08 ID'] = QLabel(str(i) + sources[src]['Virtual Patchbay Name'] + '-' + sources[src]['Patch Point Number'])
        table_layout.addWidget(r['EDIT Out SW-P-08 ID'], start_row + i, col)


def create_destination_labels(destinations, table_layout, row=0, start_col=2):
    r = {}
    for i, dst in enumerate(destinations):
        label = QLabel(str(i) + destinations[dst]['Virtual Patchbay Name'] + '-' + destinations[dst]['Patch Point Number'])
        label.setAlignment(Qt.AlignCenter)
        # https://stackoverflow.com/questions/9183050/vertical-qlabel-or-the-equivalent
        # https://stackoverflow.com/questions/3757246/pyqt-rotate-a-qlabel-so-that-its-positioned-diagonally-instead-of-horizontally
        r['EDIT In SW-P-08 ID'] = label
        table_layout.addWidget(r['EDIT In SW-P-08 ID'], row, start_col + i)


class Color(QWidget):
    def __init__(self, color):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)


class MainWindow(QMainWindow):
    def __init__(self, sources, destinations):
        super(MainWindow, self).__init__()

        self.setWindowTitle("ConnectIO")

        # Base GUI Layout
        background_layout = QGridLayout()
        grid_layout = QGridLayout()

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

        background_layout.addLayout(grid_layout, 1, 1)

        create_source_label_edit_col(sources, grid_layout)
        create_source_label_col(sources, grid_layout)
        create_destination_labels(destinations, grid_layout)

        rows = 8
        cols = 8
        start_row = 1
        start_col = 2
        for row in range(start_row, start_row + rows):
            for col in range(start_col, start_col + cols):
                grid_layout.addWidget(QPushButton("R" + str(row) + " C" + str(col)), row, col)




        widget = QWidget()
        widget.setLayout(background_layout)
        self.setCentralWidget(widget)


def main(source_list):
    app = QApplication(sys.argv)
    window = MainWindow(source_list, destination_list)
    window.show()
    app.exec()


if __name__ == '__main__':

    # - TODO - add this to settings/save  / add to GUI
    io_csv = 'VirtualPatchbays.csv'
    source_list, destination_list = import_io_from_csv(io_csv)

    #for source in source_list:
    #    print(source, source_list[source])

    main(source_list)
