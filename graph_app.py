#!/usr/bin/python3

# Import Qt Stuff
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, \
                            QWidget, QVBoxLayout, QLabel, QFileDialog
from PyQt5.QtCore import Qt

import sys, csv

from graph_view import GraphView
from graph_options import GraphOptions
from util import pack16Bit, convertTime

ID = 0
D0 = 1
D1 = 2
D2 = 3
D3 = 4
D4 = 5
D5 = 6
D6 = 7
D7 = 8
TIME = 9

voltage = 0
rear_wheel_speed = 0

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
        self.addOptionsBox()
        
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

    def addOptionsBox(self):
        self.options = GraphOptions()
        self.options.addCheckbox('Telemetry', 'MC Inlet Temperature (C)')
        self.options.addCheckbox('Telemetry', 'MC Outlet Temperature (C)')
        self.options.addCheckbox('Telemetry', 'Motor Inlet Temperature (C)')
        self.options.addCheckbox('Telemetry', 'Motor Outlet Temperature (C)')
        self.options.addCheckbox('Telemetry', 'MC Inlet Pressure (PSI)')
        self.options.addCheckbox('Telemetry', 'MC Outlet Pressure (PSI)')
        self.options.addCheckbox('Telemetry', 'Motor Inlet Pressure (PSI)')
        self.options.addCheckbox('Telemetry', 'Motor Outlet Pressure (PSI)')
        self.options.addCheckbox('Telemetry', 'Motor Speed (RPM)')

        self.options.addCheckbox('PEI', 'DC Current Draw (Amps)')
        self.options.addCheckbox('PEI', 'Power (W)')

        self.options.addCheckbox('BMS', 'Maximum Temperature (C)')
        self.options.addCheckbox('BMS', 'State Of Charge (%)')
        self.options.addCheckbox('BMS', 'Pack Voltage (V)')

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
        global voltage
        global rear_wheel_speed

        #time = convertTime(int(row[-1]))
        time = float(row[-1])
        if (row[0] == 'a5'): # Telem
            graph_view.add_data('Telemetry', 'Motor Speed (RPM)', float(row[3]), time)
            rear_wheel_speed = float(row[3]) * 12 / 33
        if (row[0] == '400'): # Telem
            graph_view.add_data('Telemetry', 'MC Inlet Temperature (C)', float(row[1]), time)
            graph_view.add_data('Telemetry', 'MC Outlet Temperature (C)', float(row[3]), time)
        if (row[0] == '387'): # PEI
            # TODO: Is it amps?
            graph_view.add_data('BMS', 'DC Current Draw (Amps)', float(row[1]), time)
            graph_view.add_data('BMS', 'Power (W)', float(row[1]) * voltage, time)
        if (row[0] == '380'): # BMS
            # TODO: Add BMS pack voltage
            graph_view.add_data('BMS', 'Maximum Temperature (C)', float(row[1]), time)
            graph_view.add_data('BMS', 'State Of Charge (%)', float(row[2]), time)
            graph_view.add_data('BMS', 'Pack Voltage (V)', float(row[5]), time)
        if(row[0] == '500'):
            graph_view.add_data('Telemetry', 'Front Strain Gauge ADC', float(row[D0]), time)
            graph_view.add_data('Telemetry', 'TC Torque Request (Nm)', float(row[D4]), time)
            fws = float(row[D2])
            graph_view.add_data('Telemetry', 'Front wheel speed (RPM)', fws, time)
            slip_ratio = 0
            if(fws > 0):
                slip_ratio = (rear_wheel_speed / fws) - 1
            graph_view.add_data('Telemetry', 'Slip Ratio', slip_ratio, time)
        if(row[0] == '766'):
            graph_view.add_data('Telemetry', 'Throttle (%)', float(row[D3]), time)
            graph_view.add_data('Telemetry', 'Brake (%)', float(row[D4]), time)
        if(row[ID] == 'c0'):
            graph_view.add_data('Telemetry', 'Torque Request (Nm)', float(row[D0]), time)
            graph_view.add_data('Telemetry', 'Power (RPM)', float(row[D0]) * rear_wheel_speed * 33 / 12 * 0.10472, time)
        if(row[ID] == '402'):
            graph_view.add_data('Telemetry', 'Inlet Pressure (PSI)', float(row[D0]), time)
            graph_view.add_data('Telemetry', 'Outlet Pressure (PSI)', float(row[D2]), time)
        if(row[ID] == '403'):
            graph_view.add_data('Telemetry', 'Rear Strain Gauge ADC', float(row[D0]), time)
        if(row[ID] == '100'):
            graph_view.add_data('Telemetry', 'Angle X (Deg)', float(row[D0]), time)
            graph_view.add_data('Telemetry', 'Angle Y (Deg)', float(row[D2]), time)
            graph_view.add_data('Telemetry', 'Angle Z (Deg)', float(row[D4]), time)
        if(row[ID] == '101'):
            graph_view.add_data('Telemetry', 'Accel X (Deg)', float(row[D0]), time)
            graph_view.add_data('Telemetry', 'Accel Y (Deg)', float(row[D2]), time)
            graph_view.add_data('Telemetry', 'Accel Z (Deg)', float(row[D4]), time)
        if(row[ID] == 'a7'):
            voltage = float(row[D0])
           
        

# Create main window
if len(sys.argv) == 1: # Load the file prompt
    app = QApplication(sys.argv)
    window = GraphApp()
    window.show()

    sys.exit(app.exec())
else:
    print("Usage: python3 graph_app.py [opt:graph_type]")