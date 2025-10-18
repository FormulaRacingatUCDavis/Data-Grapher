#!/usr/bin/python3

import matplotlib
matplotlib.use("qt5agg")
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QMainWindow, QToolBar, QAction,
    QToolButton, QMenu, QHBoxLayout, QVBoxLayout
)

from controller import Controller

class View(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FRUCD Data Grapher')
        controller = Controller()

        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)
        self.toolbar.setStyleSheet('''
            QToolButton::menu-indicator {
                image: none;
            }
        ''')

        self.log_actions = {}

        self.add_dropdown('File', {
            'Open...': self.open_log,
            'Export CSV...': controller.export_csv,
            '---': None,
            'Exit': self.close
        })
        self.add_dropdown('Plot', {
            'Add...': controller.add_plot,
            'Save As...': controller.export_plot,
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

    def open_log(self):
        """
        Load data from CSV
        """
        controller = Controller()
        controller.load_model()

        for name in [
            'Export CSV...',
            'Add...',
            'Save As...'
        ]:
            if name in self.log_actions:
                self.log_actions[name].setEnabled(True)

    def get_graph(self, data):
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
        
        # Add buttons
        self.buttonLayout = QHBoxLayout()
        for category in categories:
            # Must also wire up logic for the buttons
            button = QPushButton(category)
            button.clicked.connect(lambda _, category=category: self.switchTab(ln, ax, category))

            self.buttonLayout.addWidget(button)

        # Create the GUI stuff
        self.tab = QWidget() # Tab's contents
        self.layout = QVBoxLayout() # Tab's layout
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