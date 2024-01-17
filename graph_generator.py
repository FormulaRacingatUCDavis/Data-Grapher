import matplotlib
matplotlib.use("qt5agg") # Needed for mpl to stay open
from matplotlib import pyplot as plt

from plot_window import PlotWindow

# Data should be formed by category - type

class GraphGenerator(object):
    def __init__(self):
        self.messages = {}

    def add_data(self, channel, category, value, time):
        if not channel in self.messages:
            self.messages[channel] = {}

        if not category in self.messages[channel]:
            self.messages[channel][category] = []

        self.messages[channel][category].append((value, time))
    
    def get_graphs(self):
        plt.style.use('./viewer.mplstyle')

        graphs = []
        for channel in self.messages:
            # Create a tab
            fig, axs = plt.subplots(1, len(self.messages[channel]))
            if len(self.messages[channel]) == 1:
                axs = [axs]
                print(axs[0])

            for index, category in enumerate(self.messages[channel]):
                # Create an individual graph
                values = [message[0] for message in self.messages[channel][category]]
                times = [message[1] for message in self.messages[channel][category]]

                axs[index].set_title(category)
                axs[index].set_facecolor('#1a1a23')
                axs[index].set(xlabel='Timestamp (s)', ylabel=category)
                axs[index].plot(times, values, marker = 'o', c='#02d0f5')
                index += 1
            
            graphs.append((channel, fig))
            
        return graphs