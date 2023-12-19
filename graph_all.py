# Graphs all the data and sorts them into tabs.

import csv
from sys import argv

from can_util import convert_time, pack_16bit
from graph_viewer import GraphViewer

def parse_row(row, graph_viewer: GraphViewer):
    # Time is always the last row
    time = convert_time(int(row[-1]))

    if (row[0] == '400'): # Telem
        graph_viewer.add_data('Telemetry', 'MC Inlet Temperature (C)', int(row[1]), time)
        graph_viewer.add_data('Telemetry', 'MC Outlet Temperature (C)', int(row[2]), time)
        graph_viewer.add_data('Telemetry', 'Motor Inlet Temperature (C)', int(row[3]), time)
        graph_viewer.add_data('Telemetry', 'Motor Outlet Temperature (C)', int(row[4]), time)
        graph_viewer.add_data('Telemetry', 'MC Inlet Pressure (PSI)', int(row[5]), time)
        graph_viewer.add_data('Telemetry', 'MC Outlet Pressure (PSI)', int(row[6]), time)
        graph_viewer.add_data('Telemetry', 'Motor Inlet Pressure (PSI)', int(row[7]), time)
        graph_viewer.add_data('Telemetry', 'Motor Outlet Pressure (PSI)', int(row[8]), time)
    if (row[0] == '387'): # PEI
        # TODO: Is it amps?
        graph_viewer.add_data('PEI', 'DC Current Draw (Amps)', pack_16bit(int(row[1]), int(row[2])), time)
    if (row[0] == '380'): # BMS
        graph_viewer.add_data('BMS', 'Maximum Temperature (C)', int(row[1]), time)
        graph_viewer.add_data('BMS', 'State Of Charge (%)', int(row[2]), time)
        graph_viewer.add_data('BMS', 'MC Inlet Pressure (PSI)', pack_16bit(int(row[5]), int(row[6])) / 100, time)

def main():
    if (len(argv) != 2):
        print("Usage: graph_all.py <some_datafile.csv>")
        return

    datafile = None
    try:
        datafile = open(argv[1], 'r')
    except FileNotFoundError:
        print(f'Error: file "{argv[1]}" does not exist')
        return

    reader = csv.reader(datafile)
    g = GraphViewer()
    for row in reader:
        if (len(row) != 10):
            print(f'Graph Viewer - Warning: Unknown row "{row}"')
            continue
        else:
            parse_row(row, g)

    datafile.close()
    g.display()

if __name__ == '__main__':
    main()
