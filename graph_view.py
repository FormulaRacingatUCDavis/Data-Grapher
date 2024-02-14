import matplotlib
matplotlib.use("qt5agg") # Needed for mpl to stay open
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import pyplot as plt

from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout

# Data should be formed by category - type
class GraphView(object):
    def __init__(self, data_filter):
        self.data_filter = data_filter
        self.messages = {}
        
        self.canvases = []
        self.figure_handles = []
        self.toolbar_handles = []
        self.tab_handles = []
        self.current_window = -1
        self.tabs = QTabWidget()

    def add_data(self, channel, category, value, time):
        # Apply filter
        if channel in self.data_filter and \
            category in self.data_filter[channel] and \
            not self.data_filter[channel][category]:
            return # Ignore
        
        if not channel in self.messages:
            self.messages[channel] = {}

        if not category in self.messages[channel]:
            self.messages[channel][category] = []

        self.messages[channel][category].append((value, time))
    
    def generate(self):
        plt.style.use('./viewer.mplstyle')

        ## Initialize the widget
        for channel in self.messages:
            # Ignore empty channels
            if not channel:
                continue

            # Create a tab
            fig, axs = plt.subplots(1, len(self.messages[channel]))
            if len(self.messages[channel]) == 1:
                axs = [axs]

            for index, category in enumerate(self.messages[channel]):
                # Create an individual graph
                values = [message[0] for message in self.messages[channel][category]]
                times = [message[1] for message in self.messages[channel][category]]

                axs[index].set_title(category)
                axs[index].set_facecolor('#1a1a23')
                axs[index].set(xlabel='Timestamp (s)', ylabel=category)
                axs[index].plot(times, values, marker = 'o', c='#02d0f5')
            
            self.add_plot(channel, fig)
    
    def add_plot(self, title, figure):
        new_tab = QWidget()
        layout = QVBoxLayout()
        new_tab.setLayout(layout)

        figure.subplots_adjust(left=0.05, right=0.99, bottom=0.05, top=0.91, wspace=0.2, hspace=0.2)
        new_canvas = FigureCanvas(figure)
        new_toolbar = NavigationToolbar(new_canvas, new_tab)

        layout.addWidget(new_canvas)
        layout.addWidget(new_toolbar)
        self.tabs.addTab(new_tab, title)

        self.toolbar_handles.append(new_toolbar)
        self.canvases.append(new_canvas)
        self.figure_handles.append(figure)
        self.tab_handles.append(new_tab)
