#!/usr/bin/python3

import matplotlib
matplotlib.use("qt5agg")
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QMainWindow, QToolBar, QAction, QCheckBox,
    QToolButton, QMenu, QHBoxLayout, QVBoxLayout, QFileDialog, QLabel, QGroupBox
)
from PyQt5.QtCore import Qt

from controller import Controller

class OptionsView(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Options')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.categories = {}

        options = QGroupBox()
        self.options_layout = QHBoxLayout()
        self.options_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        options.setLayout(self.options_layout)

        self.get_options()

        load_bttn = QPushButton('Load Graphs')
        load_bttn.setMinimumHeight(50)
        load_bttn.clicked.connect(lambda: self.get_selected())

        layout.addWidget(options)
        layout.addWidget(load_bttn)

        view = QWidget()
        view.setLayout(layout)
        self.setCentralWidget(view)

    def addCheckbox(self, category, title):
        if category not in self.categories:
            vbox = QVBoxLayout()
            vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.options_layout.addLayout(vbox)

            label = QLabel(category)
            label.setAlignment(Qt.AlignmentFlag.AlignTop)
            vbox.addWidget(label)
            self.categories[category] = vbox

        checkbox = QCheckBox(title)
        checkbox.setChecked(False)
        self.categories[category].addWidget(checkbox)

    def get_options(self):
        signals = [
            "MC Inlet Temperature (C)",
            "Motor Inlet Temperature (C)",
            "MC Inlet Pressure (PSI)"
        ]

        for title in signals:
            self.addCheckbox('INV', title)

    def get_selected(self):
        print('Loading selected choices...')
        self.close()

class MainView(QMainWindow):
    def __init__(self):
        super().__init__()

        self.windows = []
        self.setWindowTitle('FRUCD Data Grapher')
        self.controller = Controller()

        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)
        self.toolbar.setStyleSheet('''
            QToolButton::menu-indicator {
                image: none;
            }
        ''')

        self.log_actions = {}

        self.add_dropdown('File', {
            'Open...': self.get_log,
            'Export CSV...': self.controller.export_csv,
            '---': None,
            'Exit': self.close
        })
        self.add_dropdown('Plot', {
            'Add...': self.get_options,
            'Save As...': self.controller.export_plot,
        })

        for name in [
            'Export CSV...', 
            'Add...', 
            'Save As...'
            ]:
            if name in self.log_actions:
                self.log_actions[name].setEnabled(False)

        self.showMaximized()

    def add_dropdown(self, name, actions: dict):
        """
        Helper function for adding to toolbar
        """
        button = QToolButton()
        button.setText(name)
        button.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(button)

        for label, handler in actions.items():
            if label == '---':
                menu.addSeparator()
                continue
            action = QAction(label, self)
            if handler is not None:
                action.triggered.connect(handler)
            menu.addAction(action)

            self.log_actions[label] = action

        button.setMenu(menu)
        self.toolbar.addWidget(button)

    def get_log(self):
        """
        Open File Explorer view to choose log file
        """
        selector = QFileDialog(self)
        selector.setNameFilter('*.csv')
        if selector.exec():
            file = selector.selectedFiles()[0]
            self.controller.load_log(file)

        for name in [
            'Export CSV...',
            'Add...',
            'Save As...'
        ]:
            if name in self.log_actions:
                self.log_actions[name].setEnabled(True)

    def get_options(self):
        """
        Open checkbox view to select graphing options
        """
        options = OptionsView()
        self.windows.append(options)
        options.show()

    def get_graph(self):
        data = self.controller.model.data
        categories = [category for category in data]

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_title(categories[0])
        ax.set_facecolor('#1a1a23')
        ax.set(xlabel='Timestamp (s)', ylabel=categories[0])
        ax.autoscale(True)
        fig.subplots_adjust(left=0.05, right=0.99, bottom=0.075, top=0.91, wspace=0.2, hspace=0.2)

        ln, = ax.plot(
            [message[1] for message in self.channelMessages[categories[0]]], 
            [message[0] for message in self.channelMessages[categories[0]]],
            marker='o', c='#02d0f5')
        
        self.buttonLayout = QHBoxLayout()
        for category in categories:
            button = QPushButton(category)
            button.clicked.connect(lambda _, category=category: self.switchTab(ln, ax, category))

            self.buttonLayout.addWidget(button)

        # Create the GUI stuff
        self.tab = QWidget()
        self.layout = QVBoxLayout()
        self.tab.setLayout(self.layout)

        self.canvas = FigureCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, )
        
        self.layout.addLayout(self.buttonLayout)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)

    def switchTab(self, ln, ax, category):
        times = []
        values = []
        for message in self.channelMessages[category]:
            values.append(message[0])
            times.append(message[1])

        ln.set_xdata(times)
        ln.set_ydata(values)
        ax.set(ylabel=category)
        ax.relim()
        ax.autoscale_view()
        plt.draw()
        self.canvas.draw()
        self.canvas.flush_events()