from PyQt5.QtWidgets import QHBoxLayout, QGroupBox, QFileDialog
from model import Model

"""Contains the options for creating the graph, as well as their UI"""
class Controller(object):
    def __init__(self):
        self.categories = {}
        self.layout = QHBoxLayout()

        self.box = QGroupBox("Options")
        self.box.adjustSize()
        self.box.setLayout(self.layout)

    def load_model(self):
        """
        Helper function for adding to toolbar
        """
        selector = QFileDialog(self)
        selector.setNameFilter('*.csv')
        if selector.exec():
            file = selector.selectedFiles()[0]
            self.controller.parse_log(file)

    def export_csv(self):
        print('Export CSV clicked')

    def add_plot(self):
        print('Add Plot clicked')

    def export_plot(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Save Graph', '', 'PNG Files (*.png);;All Files (*)'
        )
        if file_path:
            print(f'Graph would be saved to {file_path}')