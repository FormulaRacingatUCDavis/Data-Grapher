#!/usr/bin/python3

import matplotlib
import numpy as np
matplotlib.use("qt5agg")
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QMainWindow, QToolBar, QAction, QCheckBox,
    QToolButton, QMenu, QHBoxLayout, QVBoxLayout, QFileDialog, QGroupBox,
    QScrollArea, QSlider, QLabel, QSizePolicy
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

        # store last plotted datasets so we can re-plot on slider change
        self.current_datasets = []
        self.threshold = 0  # default threshold

        # --- threshold slider + label ---
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(1)    # min threshold value
        self.threshold_slider.setMaximum(100)  # max threshold value
        self.threshold_slider.setValue(int(self.threshold))
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.setTickInterval(5)

        self.threshold_label = QLabel(f"Threshold: {self.threshold:.1f}")

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Δ threshold"))
        slider_layout.addWidget(self.threshold_slider)
        slider_layout.addWidget(self.threshold_label)

        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        # -------------------------------

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addLayout(slider_layout)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def on_threshold_changed(self, value):
        # Update threshold and label
        self.threshold = float(value)
        self.threshold_label.setText(f"Threshold: {self.threshold:.1f}")

        # Re-plot with new threshold if we have data
        if self.current_datasets:
            self._plot_with_threshold(self.current_datasets)

    def plot_signals(self, datasets):
        """
        External entry from MainView.
        Save datasets and plot using current threshold.
        """
        self.current_datasets = datasets
        self._plot_with_threshold(datasets)

class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.fig = plt.Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Data + thresholds
        self.current_datasets = []       # list of (name, t, y)
        self.thresholds = []             # per-plot threshold values
        self.slider_widgets = []         # list of (slider, label)

        # Container for per-plot sliders
        self.controls_widget = QWidget()
        self.controls_layout = QVBoxLayout()
        self.controls_widget.setLayout(self.controls_layout)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.controls_widget)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    # -----------------------------
    # Public entry point
    # -----------------------------
    def plot_signals(self, datasets):
        """
        Called from MainView.
        Builds per-plot sliders and draws the plots.
        """
        self.current_datasets = datasets or []
        self._build_sliders()
        self._plot_all()

    # -----------------------------
    # Slider + threshold handling
    # -----------------------------
    def _build_sliders(self):
        # Clear old sliders
        while self.controls_layout.count():
            item = self.controls_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        self.thresholds = []
        self.slider_widgets = []

        # Create one slider row per dataset
        for idx, (name, t, y) in enumerate(self.current_datasets):
            row_widget = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_widget.setLayout(row_layout)

            label = QLabel(f"{name} Δ threshold")
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setValue(0)  # default
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(5)

            value_label = QLabel("0.0")

            # Capture idx in default arg to avoid late-binding
            slider.valueChanged.connect(
                lambda val, i=idx: self.on_threshold_changed(i, val)
            )

            row_layout.addWidget(label)
            row_layout.addWidget(slider)
            row_layout.addWidget(value_label)

            self.controls_layout.addWidget(row_widget)

            self.thresholds.append(float(slider.value()))
            self.slider_widgets.append((slider, value_label))

    def on_threshold_changed(self, index, value):
        # update internal threshold + label
        th = float(value)
        self.thresholds[index] = th
        slider, value_label = self.slider_widgets[index]
        value_label.setText(f"{th:.1f}")

        # re-plot everything with updated thresholds
        self._plot_all()

    # -----------------------------
    # Plotting
    # -----------------------------

    def _plot_all(self):
        self.fig.clear()

        if not self.current_datasets:
            self.canvas.draw()
            return

        n_plots = len(self.current_datasets)
        axes = self.fig.subplots(n_plots, 1)
        if n_plots == 1:
            axes = [axes]

        for i, (name, t, y) in enumerate(self.current_datasets):
            ax = axes[i]
            t = np.asarray(t)
            y = np.asarray(y)

            threshold = self.thresholds[i] if i < len(self.thresholds) else 5.0

            # ---- change-threshold thinning vs last kept point ----
            if len(y) == 0:
                t_f = np.asarray(t)
                y_f = np.asarray(y)
            else:
                t_f = [t[0]]
                y_f = [y[0]]
                last_val = y[0]

                for k in range(1, len(y)):
                    if abs(y[k] - last_val) >= threshold:
                        t_f.append(t[k])
                        y_f.append(y[k])
                        last_val = y[k]

                t_f = np.array(t_f)
                y_f = np.array(y_f)

                # ---- moving average filter on y_f only ----
                window_size = min(5, len(y_f))  # or whatever window you want
                if window_size > 1:
                    weight = np.ones(window_size) / window_size
                    # keep the same length; 'same' centers the window
                    y_f = np.convolve(y_f, weight, mode='same')
                    # leave t_f alone so time axis stays correct
                
      
                

            # ------------------------------------------------------

            ax.set_title(name)

            # Plot filtered points only, dots only
            ax.plot(
                t_f, y_f,
                marker='o',
                markersize=2,
                linestyle='None'
            )

            # Stats from FILTERED data
            if len(y_f) > 0:
                y_min = float(np.min(y_f))
                y_max = float(np.max(y_f))

                log_rate = None
                if len(t) > 1:
                    dt = np.diff(t)
                    med_dt = float(np.mean(dt))
                    if med_dt > 0:
                        log_rate = 1.0 / med_dt  # Hz

                stats_text = (
                    f"Min: {y_min:.2f}\n"
                    f"Max: {y_max:.2f}\n"
                    f"Log Rate: {log_rate:.2f}"
                )

                ax.text(
                    0.02, 0.98, stats_text,
                    transform=ax.transAxes,
                    fontsize=10,
                    va='top',
                    bbox=dict(
                        facecolor='white',
                        alpha=0.7,
                        edgecolor='black'
                    )
                )

            ax.set_ylabel(name)
            ax.set_xlabel("Time [s]")
            ax.grid(True)
            ax.relim()
            ax.autoscale_view()

        self.fig.tight_layout()
        self.canvas.draw()