
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QCheckBox, QGroupBox, QLabel

from PyQt5.QtCore import Qt

"""Contains the options for creating the graph, as well as their UI"""
class GraphOptions(object):

    def __init__(self):
        self.categories = {}
        self.layout = QHBoxLayout()

        self.box = QGroupBox("Options")
        self.box.adjustSize()
        self.box.setLayout(self.layout)

    def addCheckbox(self, category, title):
        if category not in self.categories:
            # Add the UI and create the category
            self.categories[category] = QVBoxLayout()
            self.layout.addLayout(self.categories[category])

            label = QLabel(category)
            label.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.categories[category].addWidget(label)
        
        box = QCheckBox(title)
        box.setChecked(True)
        self.categories[category].addWidget(box)
        self.getSelected()
    
    def getSelected(self):
        """Returns the selected options for each channel"""
        res = {}
        for cat in self.categories:
            res[cat] = {}
            items = [self.categories[cat].itemAt(i) for i in range(self.categories[cat].count())]

            for item in items:
                # Ignore the labels
                if type(item.widget()) is not QCheckBox:
                    continue

                option = item.widget().text()
                res[cat][option] = item.widget().isChecked()
        return res