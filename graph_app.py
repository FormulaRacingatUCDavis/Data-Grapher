#!/usr/bin/python3

# Import Qt Stuff
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, \
                            QWidget, QTabWidget, QVBoxLayout, \
                            QLabel, QFileDialog, \
                            QGroupBox, QHBoxLayout
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

import sys, csv

from graph_view import GraphView
from graph_options import GraphOptions
from util import pack16Bit, convertTime

class GraphApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle("FRUCD Graph App")
        self.setGeometry(100, 100, 800, 600)

        # Display title
        header = QLabel()
        header.setAlignment(Qt.AlignCenter)
        header.setText("FRUCD Data Grapher")
        header.adjustSize()

        # Add options box
        self.options = GraphOptions()
        self.options.addCheckbox('Telemetry', 'MC Inlet Temperature (C)')
        self.options.addCheckbox('Telemetry', 'MC Outlet Temperature (C)')
        self.options.addCheckbox('Telemetry', 'Motor Inlet Temperature (C)')
        self.options.addCheckbox('Telemetry', 'Motor Outlet Temperature (C)')
        self.options.addCheckbox('Telemetry', 'MC Inlet Pressure (PSI)')
        self.options.addCheckbox('Telemetry', 'MC Outlet Pressure (PSI)')
        self.options.addCheckbox('Telemetry', 'Motor Inlet Pressure (PSI)')
        self.options.addCheckbox('Telemetry', 'Motor Outlet Pressure (PSI)')

        self.options.addCheckbox('PEI', 'DC Current Draw (Amps)')

        self.options.addCheckbox('BMS', 'Maximum Temperature (C)')
        self.options.addCheckbox('BMS', 'State Of Charge (%)')
        self.options.addCheckbox('BMS', 'MC Inlet Pressure (PSI)')
        
        load = QPushButton()
        load.setText("Load from CSV")
        load.setMinimumHeight(50)
        load.clicked.connect(lambda: self.loadButtonPressed())

        # Box layout
        layout = QVBoxLayout()
        layout.addWidget(header)
        layout.addWidget(self.options.box)
        layout.addWidget(load)
        
        self.view = QWidget()
        self.view.setLayout(layout)
        self.setCentralWidget(self.view)

    def loadButtonPressed(self):
        fileSelector = QFileDialog(self)
        fileSelector.setNameFilter("*.csv")

        if fileSelector.exec():
            fileSelected = fileSelector.selectedFiles()[0]
            # Load into a plot window
            self.loadGraph(fileSelected)
    
    def loadGraph(self, fileSelected):
        datafile = None
        try:
            datafile = open(fileSelected, 'r')
        except FileNotFoundError:
            print(f'Error: file "{fileSelected}" does not exist')
            return

        reader = csv.reader(datafile)
        g = GraphView(self.options.getSelected()) # Should pass in options here as a filter
        for row in reader:
            if (len(row) != 10):
                print(f'Graph Viewer - Warning: Unknown row "{row}"')
                continue
            else:
                self.appendRow(row, g)
        g.generate()
        g.tabs.show()

        self.setCentralWidget(g.tabs)

    def appendRow(self, row, graph_view):
        time = convertTime(int(row[-1]))

        if (row[0] == '400'): # Telem
            graph_view.add_data('Telemetry', 'MC Inlet Temperature (C)', int(row[1]), time)
            graph_view.add_data('Telemetry', 'MC Outlet Temperature (C)', int(row[2]), time)
            graph_view.add_data('Telemetry', 'Motor Inlet Temperature (C)', int(row[3]), time)
            graph_view.add_data('Telemetry', 'Motor Outlet Temperature (C)', int(row[4]), time)
            graph_view.add_data('Telemetry', 'MC Inlet Pressure (PSI)', int(row[5]), time)
            graph_view.add_data('Telemetry', 'MC Outlet Pressure (PSI)', int(row[6]), time)
            graph_view.add_data('Telemetry', 'Motor Inlet Pressure (PSI)', int(row[7]), time)
            graph_view.add_data('Telemetry', 'Motor Outlet Pressure (PSI)', int(row[8]), time)
        if (row[0] == '387'): # PEI
            # TODO: Is it amps?
            graph_view.add_data('PEI', 'DC Current Draw (Amps)', pack16Bit(int(row[1]), int(row[2])), time)
        if (row[0] == '380'): # BMS
            graph_view.add_data('BMS', 'Maximum Temperature (C)', int(row[1]), time)
            graph_view.add_data('BMS', 'State Of Charge (%)', int(row[2]), time)
            graph_view.add_data('BMS', 'MC Inlet Pressure (PSI)', pack16Bit(int(row[5]), int(row[6])) / 100, time)

# Create main window
if len(sys.argv) == 1: # Load the file prompt
    app = QApplication(sys.argv)

    window = GraphApp()
    window.show()

    sys.exit(app.exec())
else:
    print("Usage: python3 graph_app.py [opt:graph_type]")