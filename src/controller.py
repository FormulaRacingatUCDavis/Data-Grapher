import csv
import cantools

from model import Model

class Controller(object):
    def __init__(self):
        self.model = Model()
        self.graph_windows = []  # Track created graph windows

    def load_log(self, file):
        """
        Load log file data to update model
        """
        frucd_dbc = cantools.database.load_file('20240129 Gen5 CAN DB.dbc')
        mc_dbc = cantools.database.load_file('FE12.dbc')

        unrecognized = set()
        count = 0

        with open(file, 'r', newline='') as raw_can:
            reader = csv.reader(raw_can)
            for row in reader:
                id = int(row[0], 16)

                message = None
                for dbc in [frucd_dbc, mc_dbc]:
                    try:
                        message = dbc.get_message_by_frame_id(id)
                        break
                    except KeyError:
                        continue
                if message is None:
                    print(f'>> Unrecognized ID {id} at timestamp: {row[-1]}')
                    unrecognized.add(id)
                    count += 1
                    continue

                data_bytes = []
                for b in row[1:9]:
                    if b.strip() == "":
                        data_bytes.append(0)
                    else:
                        try:
                            data_bytes.append(int(b))
                        except ValueError:
                            data_bytes.append(0)

                raw_data = bytes(data_bytes)
                timestamp = float(row[-1]) / 1000.0
                decoded = message.decode(raw_data)

                self.model.get_data(
                    timestamp,
                    message.senders[0],
                    id,
                    message.name,
                    decoded
                )
        
        print('Completed parsing.')

    def export_csv(self):
        print('Export CSV clicked')

    def add_plot(self):
        print('Add plot clicked')

    def export_plot(self):
        print('Export plot clicked')
    
    def create_graphs(self, selected_signals):
        """
        Create GraphView windows for selected signals, grouped by source
        """
        # Import here to avoid circular import issues
        from view import GraphView
        
        # Group signals by source
        signals_by_source = {}
        for item in selected_signals:
            source = item['source']
            signal = item['signal']
            if source not in signals_by_source:
                signals_by_source[source] = []
            signals_by_source[source].append(signal)
        
        # Create a GraphView window for each source
        for source, signals in signals_by_source.items():
            graph_window = GraphView(source, signals, self.model.data)
            self.graph_windows.append(graph_window)
            graph_window.show()