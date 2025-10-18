from PyQt5.QtWidgets import QApplication
import sys

from view import View

# Create main window
if len(sys.argv) == 1: # Load the file prompt
    app = QApplication(sys.argv)
    window = View()
    window.show()

    sys.exit(app.exec())
else:
    print("Usage: python3 graph_app.py [opt:graph_type]")