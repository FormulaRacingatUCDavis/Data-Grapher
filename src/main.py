from PyQt5.QtWidgets import QApplication
import sys

from view import MainView

if len(sys.argv) == 1:
    app = QApplication(sys.argv)
    window = MainView()
    window.show()
    sys.exit(app.exec())
else:
    print("Usage: python3 graph_app.py [opt:graph_type]")