import matplotlib
matplotlib.use("qt5agg") # Needed for mpl to stay open
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import pyplot as plt

from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton

from graph_tab import GraphTab

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
        self.graphTabs = []

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

            graphTab = GraphTab(self.messages[channel])
            self.tabs.addTab(graphTab.tab, channel)
            self.graphTabs.append(graphTab)

