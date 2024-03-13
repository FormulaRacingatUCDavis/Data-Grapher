import matplotlib
matplotlib.use("qt5agg") # Needed for mpl to stay open
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import pyplot as plt

from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton

"""Custom tab that supports switching the data on its figure."""
class GraphTab(object):
    def __init__(self, channelMessages):
        self.channelMessages = channelMessages

        categories = [category for category in channelMessages]

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
        print(category)
        times = [message[1] for message in self.channelMessages[category]], 
        values = [message[0] for message in self.channelMessages[category]],

        ln.set_xdata(times)
        ln.set_ydata(values)
        ax.set_title(category)
        ax.relim()
        ax.autoscale_view()
        plt.draw()
        self.canvas.draw()
        self.canvas.flush_events()