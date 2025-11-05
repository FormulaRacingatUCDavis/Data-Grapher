#!/usr/bin/python3

import matplotlib
matplotlib.use("qt5agg")
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QMainWindow, QToolBar, QAction, QCheckBox,
    QToolButton, QMenu, QHBoxLayout, QVBoxLayout, QFileDialog, QLabel, QGroupBox,
    QScrollArea
)
from PyQt5.QtCore import Qt

from controller import Controller

class OptionsView(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self.setWindowTitle('Options')
        self.setGeometry(100, 100, 600, 400)

        # Create main layout
        main_layout = QVBoxLayout()

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create scroll content widget
        scroll_content = QWidget()
        self.options_layout = QVBoxLayout()  # Changed from QHBoxLayout to QVBoxLayout
        self.options_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_content.setLayout(self.options_layout)

        # Set the scroll content
        scroll_area.setWidget(scroll_content)

        self.get_options()

        load_bttn = QPushButton('Load Graphs')
        load_bttn.setMinimumHeight(50)
        load_bttn.clicked.connect(lambda: self.get_selected())

        # Add widgets to main layout
        main_layout.addWidget(scroll_area)
        main_layout.addWidget(load_bttn)

        view = QWidget()
        view.setLayout(main_layout)
        self.setCentralWidget(view)

    def get_options(self):
        for src, signals in self.controller.model.graphable.items():
            # Create a group box for each source
            group_box = QGroupBox(src)
            group_layout = QVBoxLayout()
            group_box.setLayout(group_layout)
            
            # Add checkboxes for each signal in this source
            for signal in signals:
                checkbox = QCheckBox(signal)
                checkbox.setChecked(False)
                group_layout.addWidget(checkbox)
            
            # Add the group box to the main options layout
            self.options_layout.addWidget(group_box)

    def get_selected(self):
        print('Loading selected choices...')
        selected_signals = []
        
        # Collect all selected checkboxes
        for i in range(self.options_layout.count()):
            widget = self.options_layout.itemAt(i).widget()
            if isinstance(widget, QGroupBox):
                group_layout = widget.layout()
                for j in range(group_layout.count()):
                    checkbox = group_layout.itemAt(j).widget()
                    if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                        selected_signals.append({
                            'source': widget.title(),
                            'signal': checkbox.text()
                        })
        
        print(f"Selected signals: {selected_signals}")
        
        # Create graphs for selected signals
        if selected_signals:
            self.controller.create_graphs(selected_signals)
        
        self.close()

class GraphView(QMainWindow):
    def __init__(self, source, signals, data):
        super().__init__()
        self.source = source
        self.signals = signals
        self.data = data
        
        self.setWindowTitle(f'Graphs - {source}')
        self.setGeometry(200, 200, 800, 600)
        
        # Create main layout
        main_layout = QVBoxLayout()
        
        # Create matplotlib figure
        self.fig, self.axes = plt.subplots(len(signals), 1, figsize=(10, 6))
        if len(signals) == 1:
            self.axes = [self.axes]  # Make it a list for consistency
        
        # Plot each signal
        for i, signal in enumerate(signals):
            self.plot_signal(i, signal)
        
        # Create canvas and toolbar
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Add to layout
        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.canvas)
        
        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Adjust layout
        self.fig.tight_layout()
    
    def plot_signal(self, index, signal):
        """
        Plot a specific signal
        """
        ax = self.axes[index]
        
        # Extract data for this signal
        timestamps = []
        values = []
        
        for entry in self.data:
            if entry['Source'] == self.source:
                # Look for the signal in the data
                signal_key = f"{self.source}_{signal}"
                if signal_key in entry['Data']:
                    timestamps.append(entry['Timestamp'])
                    values.append(entry['Data'][signal_key])
        
        if timestamps and values:
            ax.plot(timestamps, values, marker='o', markersize=2, linewidth=1)
            ax.set_title(f'{signal}')
            ax.set_xlabel('Timestamp (s)')
            ax.set_ylabel(signal)
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, f'No data found for {signal}', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes)
            ax.set_title(f'{signal} (No Data)')

class MainView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = Controller()

        self.windows = []
        self.setWindowTitle('FRUCD Data Grapher')

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
            'Save As...': self.controller.export_csv,
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
        options = OptionsView(self.controller)
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