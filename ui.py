#!/usr/bin/python3

'''
git add .
git commit -m "comment"
git origin main push
'''

import matplotlib
import numpy as np
matplotlib.use("qt5agg")
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QMainWindow, QToolBar, QAction, QCheckBox,
    QToolButton, QMenu, QHBoxLayout, QVBoxLayout, QFileDialog, QGroupBox,
    QScrollArea, QSlider, QLabel, QSizePolicy, QComboBox, QDoubleSpinBox
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

        self.add_dropdown('File', {
            'Open...': self.get_log,
            'Export CSV...': self.export_csv,
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
        button = QToolButton()
        button.setText(name)
        button.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(button)

        for label, handler in actions.items():
            if label == '---':
                menu.addSeparator()
                continue
            action = QAction(label, self)
            action.triggered.connect(handler)
            menu.addAction(action)

        button.setMenu(menu)
        self.toolbar.addWidget(button)
        return button

    def get_log(self):
        selector = QFileDialog(self)
        selector.setNameFilter('*.csv')
        if selector.exec():
            file = selector.selectedFiles()[0]
            self.controller.load_log(file)

            self.graphs.fig.clear()
            self.graphs.canvas.draw()

            self.plot_menu.setEnabled(True)

    def get_graphs(self):
        self.options = OptionsView(self.controller)
        self.options.done.connect(self.display_graphs)
        self.options.get_options()

    def display_graphs(self, payload):
        datasets = []

        ts_selected = payload.get("timeseries", {})
        datasets.extend(self.controller.get_datasets(ts_selected))

        xy = payload.get("xy", None)
        if xy and xy.get("enabled"):
            ds = self.controller.get_xy_dataset(
                xy.get("x_sel"),
                xy.get("y_sel"),
                xy.get("dt", 0.02),
            )
            if ds is not None:
                datasets.append(ds)

        self.graphs.plot_signals(datasets)

    def export_csv(self):
        selector = QFileDialog(self)
        selector.setNameFilter('*.csv')
        selector.setWindowTitle('Select CAN Log A')
        if not selector.exec():
            return
        file_a = selector.selectedFiles()[0]

        selector = QFileDialog(self)
        selector.setNameFilter('*.csv')
        selector.setWindowTitle('Select CAN Log B')
        if not selector.exec():
            return
        file_b = selector.selectedFiles()[0]

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save merged log as...",
            "merged_log.csv",
            "CSV Files (*.csv)"
        )
        if not out_path:
            return

        self.controller.export_csv(file_a, file_b, out_path)


class OptionsView(QMainWindow):
    done = pyqtSignal(object)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.selected = None
        self.signal_map = {}

        self.setWindowTitle('Options')
        self.setGeometry(100, 100, 900, 600)

        main_layout = QVBoxLayout()

        # ---- XY controls (simple) ----
        xy_group = QGroupBox("XY Plot (Zero-Order Hold Resample)")
        xy_layout = QHBoxLayout()
        xy_group.setLayout(xy_layout)

        self.xy_enable = QCheckBox("Enable")
        self.xy_enable.setChecked(False)

        self.x_combo = QComboBox()
        self.y_combo = QComboBox()
        self.x_combo.setEnabled(False)
        self.y_combo.setEnabled(False)

        self.dt_spin = QDoubleSpinBox()
        self.dt_spin.setDecimals(3)
        self.dt_spin.setRange(0.001, 5.000)
        self.dt_spin.setSingleStep(0.005)
        self.dt_spin.setValue(0.020)
        self.dt_spin.setEnabled(False)

        self.xy_enable.stateChanged.connect(self._on_xy_toggle)

        xy_layout.addWidget(self.xy_enable)
        xy_layout.addWidget(QLabel("X:"))
        xy_layout.addWidget(self.x_combo)
        xy_layout.addWidget(QLabel("Y:"))
        xy_layout.addWidget(self.y_combo)
        xy_layout.addWidget(QLabel("dt [s]:"))
        xy_layout.addWidget(self.dt_spin)

        main_layout.addWidget(xy_group)
        # -------------------------------

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

    def _on_xy_toggle(self):
        en = self.xy_enable.isChecked()
        self.x_combo.setEnabled(en)
        self.y_combo.setEnabled(en)
        self.dt_spin.setEnabled(en)

    def get_options(self):
        self.selected = {}
        self.x_combo.clear()
        self.y_combo.clear()

        for src, messages in self.controller.numerical.items():
            for message_name, signal_set in messages.items():
                for sig in sorted(list(signal_set)):
                    label = f"{src} | {message_name} | {sig}"
                    value = (src, message_name, sig)

                    self.x_combo.addItem(label)
                    self.x_combo.setItemData(self.x_combo.count() - 1, value)

                    self.y_combo.addItem(label)
                    self.y_combo.setItemData(self.y_combo.count() - 1, value)

        # default Y different from X if possible
        if self.y_combo.count() > 1:
            self.y_combo.setCurrentIndex(1)

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

                for sig in sorted(list(signal_list)):
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

        xy_payload = {"enabled": False}
        if self.xy_enable.isChecked() and self.x_combo.count() and self.y_combo.count():
            xy_payload = {
                "enabled": True,
                "x_sel": self.x_combo.currentData(),
                "y_sel": self.y_combo.currentData(),
                "dt": float(self.dt_spin.value()),
            }

        payload = {
            "timeseries": self.selected,
            "xy": xy_payload,
        }

        self.done.emit(payload)
        self.close()


class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.fig = plt.Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.canvas.hide()

        self.current_datasets = []   # datasets
        self.windows = []            # per-plot MA window sizes (time-series only)
        self.slider_widgets = []     # [(slider, value_label)]

        self.dark_mode_cb = QCheckBox("Dark Mode")
        self.dark_mode_cb.setChecked(False)
        self.dark_mode_cb.stateChanged.connect(self._plot_all)

        self.controls_widget = QWidget()
        self.controls_layout = QVBoxLayout()
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_widget.setLayout(self.controls_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.dark_mode_cb)
        layout.addWidget(self.controls_widget)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot_signals(self, datasets):
        self.current_datasets = datasets or []
        self.canvas.show()
        self._build_sliders()
        self._plot_all()

    def _build_sliders(self):
        while self.controls_layout.count():
            item = self.controls_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        self.windows = []
        self.slider_widgets = []

        # sliders only for time-series datasets
        ts_list = [ds for ds in self.current_datasets if len(ds) >= 4 and ds[3] == "ts"]

        for idx, (name, _, _, _) in enumerate(ts_list):
            row = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row.setLayout(row_layout)

            label = QLabel(f"{name} MA Window Size")

            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(1)
            slider.setMaximum(500)
            slider.setValue(25)
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(25)

            value_label = QLabel(str(slider.value()))

            slider.valueChanged.connect(lambda val, i=idx: self.on_window_changed(i, val))

            row_layout.addWidget(label)
            row_layout.addWidget(slider)
            row_layout.addWidget(value_label)

            self.controls_layout.addWidget(row)

            self.windows.append(int(slider.value()))
            self.slider_widgets.append((slider, value_label))

    def on_window_changed(self, index, value):
        w = int(value)
        if 0 <= index < len(self.windows):
            self.windows[index] = w
        if 0 <= index < len(self.slider_widgets):
            _, value_label = self.slider_widgets[index]
            value_label.setText(str(w))
        self._plot_all()

    def _moving_average(self, y, window):
        y = np.asarray(y)
        if y.size == 0:
            return y
        window = max(1, min(int(window), y.size))
        if window == 1:
            return y
        kernel = np.ones(window) / window
        return np.convolve(y, kernel, mode="same")

    def _plot_all(self):
        self.fig.clear()

        dark = self.dark_mode_cb.isChecked()
        self.fig.patch.set_facecolor("#121212" if dark else "white")

        if not self.current_datasets:
            self.canvas.draw()
            return

        text_color = "white" if dark else "black"
        grid_color = "#444444" if dark else "#cccccc"

        ts_list = [ds for ds in self.current_datasets if len(ds) >= 4 and ds[3] == "ts"]
        xy_list = [ds for ds in self.current_datasets if len(ds) >= 4 and ds[3] == "xy"]

        # total plots = time-series + xy plots
        n = len(ts_list) + len(xy_list)
        axes = self.fig.subplots(n, 1)
        if n == 1:
            axes = [axes]

        ax_i = 0

        # --- time-series plots ---
        for i, (name, t, y, _) in enumerate(ts_list):
            ax = axes[ax_i]
            ax_i += 1

            t = np.asarray(t, dtype=float)
            y = np.asarray(y, dtype=float)

            window = self.windows[i] if i < len(self.windows) else 1
            y_f = self._moving_average(y, window)

            ax.set_facecolor("#121212" if dark else "white")
            ax.plot(t, y_f, linewidth=1)

            ax.set_title(name, color=text_color)
            ax.set_xlabel("Time [s]", color=text_color)
            ax.set_ylabel(name, color=text_color)
            ax.tick_params(colors=text_color)
            ax.grid(True, color=grid_color)

            if y_f.size > 0:
                y_min = float(np.nanmin(y_f))
                y_max = float(np.nanmax(y_f))

                log_rate = None
                if t.size > 1:
                    dt = np.diff(t)
                    dt = dt[np.isfinite(dt)]
                    dt = dt[dt > 0]
                    if dt.size:
                        mean_dt = float(np.mean(dt))
                        if mean_dt > 0:
                            log_rate = 1.0 / mean_dt

                stats_text = (
                    f"Min: {y_min:.2f}\n"
                    f"Max: {y_max:.2f}\n"
                    f"MA Window: {window}\n"
                    + (f"Polling Rate: {log_rate:.2f} Hz" if log_rate is not None else "Polling Rate: N/A")
                )

                ax.text(
                    0.02, 0.98,
                    stats_text,
                    transform=ax.transAxes,
                    va="top",
                    color=text_color,
                    bbox=dict(
                        facecolor="#1e1e1e" if dark else "white",
                        alpha=0.85,
                        edgecolor=grid_color
                    )
                )

            ax.relim()
            ax.autoscale_view()

        # --- XY plots ---
        for ds in xy_list:
            ax = axes[ax_i]
            ax_i += 1

            # (name, x, y, "xy", xlabel, ylabel)
            name, x, y, _, xlabel, ylabel = ds
            x = np.asarray(x, dtype=float)
            y = np.asarray(y, dtype=float)

            ax.set_facecolor("#121212" if dark else "white")
            ax.scatter(x, y, s=6)

            ax.set_title(name, color=text_color)
            ax.set_xlabel(xlabel, color=text_color)
            ax.set_ylabel(ylabel, color=text_color)
            ax.tick_params(colors=text_color)
            ax.grid(True, color=grid_color)

            if x.size > 0 and y.size > 0:
                ax.text(
                    0.02, 0.98,
                    f"N: {x.size}",
                    transform=ax.transAxes,
                    va="top",
                    color=text_color,
                    bbox=dict(
                        facecolor="#1e1e1e" if dark else "white",
                        alpha=0.85,
                        edgecolor=grid_color
                    )
                )

        self.fig.tight_layout()
        self.canvas.draw()