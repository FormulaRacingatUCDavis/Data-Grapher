#!/usr/bin/python3

import matplotlib
matplotlib.use("qt5agg")
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QMainWindow, QToolBar, QAction, QCheckBox,
    QToolButton, QMenu, QHBoxLayout, QVBoxLayout, QFileDialog, QGroupBox,
    QScrollArea
)

from PyQt5.QtCore import Qt, pyqtSignal
from controller import Controller

class MainView(QMainWindow):
    def __init__(self):
        super().__init__()
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

        self.plot_menu = self.add_dropdown('Plot', {
            'Add...': self.get_graphs
        })
        self.plot_menu.setEnabled(False)

        self.graphs = GraphWidget()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.graphs)

        self.setCentralWidget(self.scroll)

        self.showMaximized()

    def add_dropdown(self, name, actions: dict):
        """
        Add dropdown menu to toolbar
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
        return button

    def get_log(self):
        """
        Open up file explorer to select raw CAN log
        """
        selector = QFileDialog(self)
        selector.setNameFilter('*.csv')
        if selector.exec():
            file = selector.selectedFiles()[0]
            self.controller.load_log(file)

            self.graphs.fig.clear()
            self.graphs.canvas.draw()

        self.plot_menu.setEnabled(True)

    def get_graphs(self):
        """
        Select decoded CAN signal(s) to graph
        """
        self.options = OptionsView(self.controller)
        self.options.done.connect(self.display_graphs)
        self.options.get_options()

    def display_graphs(self, selected):
        """
        Delete any previous graph(s) then output graph(s) to the main window
        """
        self.graphs.plot_signals(self.controller.get_datasets(selected))

class OptionsView(QMainWindow):
    done = pyqtSignal(object)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.selected = None

        self.setWindowTitle('Options')
        self.setGeometry(100, 100, 900, 600)

        main_layout = QVBoxLayout()

        menu = QWidget()
        self.menu_layout = QHBoxLayout()
        self.menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        menu.setLayout(self.menu_layout)

        load_bttn = QPushButton('Load Graphs')
        load_bttn.setMinimumHeight(50)
        load_bttn.clicked.connect(self.get_selected)

        main_layout.addWidget(menu)
        main_layout.addWidget(load_bttn)

        view = QWidget()
        view.setLayout(main_layout)
        self.setCentralWidget(view)

    def get_options(self):
        """
        Display numerical data options based on current model
        """
        self.selected = {}

        from PyQt5.QtWidgets import QSizePolicy

        for src, messages in self.controller.numerical.items():
            options = QGroupBox(src)
            options_layout = QVBoxLayout()
            options.setLayout(options_layout)

            for message_name, signal_list in messages.items():
                msg_group = QGroupBox(message_name)
                msg_layout = QVBoxLayout()
                msg_layout.setSpacing(2)
                msg_group.setLayout(msg_layout)

                msg_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

                for sig in signal_list:
                    cb = QCheckBox(sig)
                    cb.setChecked(False)
                    msg_layout.addWidget(cb)

                options_layout.addWidget(msg_group)

            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)

            scroll_content = QWidget()
            content_layout = QVBoxLayout()
            scroll_content.setLayout(content_layout)

            content_layout.addWidget(options)
            content_layout.addStretch()

            scroll_area.setWidget(scroll_content)

            self.menu_layout.addWidget(scroll_area)

        self.show()

    def get_selected(self):
        """
        Update selected options based on user input then signal when done
        """
        self.selected = {}

        for i in range(self.menu_layout.count()):
            scroll_area = self.menu_layout.itemAt(i).widget()
            if not isinstance(scroll_area, QScrollArea):
                continue

            scroll_content = scroll_area.widget()
            content_layout = scroll_content.layout()

            src_group = content_layout.itemAt(0).widget()
            src_name = src_group.title()

            if src_name not in self.selected:
                self.selected[src_name] = {}

            src_layout = src_group.layout()

            for j in range(src_layout.count()):
                msg_group = src_layout.itemAt(j).widget()
                msg_name = msg_group.title()
                msg_layout = msg_group.layout()

                for k in range(msg_layout.count()):
                    cb = msg_layout.itemAt(k).widget()
                    if isinstance(cb, QCheckBox) and cb.isChecked():

                        if msg_name not in self.selected[src_name]:
                            self.selected[src_name][msg_name] = []

                        self.selected[src_name][msg_name].append(cb.text())

        self.done.emit(self.selected)
        self.close()

class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.fig = plt.Figure(figsize=(10, 8))

        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot_signals(self, datasets):
        """
        Plot test signals on a rows x 1 grid using the figure
        """
        self.fig.clear()
        axes = self.fig.subplots(len(datasets), 1)

        if len(datasets) == 1:
            axes = [axes]

        for i in range(len(datasets)):
            axes[i].set_title(datasets[i][0])
            axes[i].plot(
                datasets[i][1],
                datasets[i][2],
                marker='o',
                linestyle='None'
            )
            axes[i].set_ylabel(datasets[i][0])
            axes[i].set_xlabel("Time [s]")

            axes[i].grid(True)
            axes[i].relim()
            axes[i].autoscale_view()

        self.fig.tight_layout()
        self.canvas.draw()