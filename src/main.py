import sys
import os

os.environ['MPLBACKEND'] = 'Qt5Agg'

if sys.platform == 'darwin':
    if 'QT_QPA_PLATFORM' not in os.environ:
        os.environ['QT_QPA_PLATFORM'] = 'cocoa'
    
    if 'QT_QPA_PLATFORM_PLUGIN_PATH' not in os.environ:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        
        venv_plugin_path = None
        venv_lib = os.path.join(project_root, 'formula', 'lib')
        if os.path.exists(venv_lib):
            for item in os.listdir(venv_lib):
                if item.startswith('python'):
                    potential_path = os.path.join(venv_lib, item, 'site-packages', 'PyQt5', 'Qt5', 'plugins')
                    if os.path.exists(potential_path):
                        venv_plugin_path = potential_path
                        break
        
        qt_plugin_paths = [
            venv_plugin_path,
            '/opt/homebrew/lib/qt5/plugins',
            '/usr/local/lib/qt5/plugins',
            '/usr/lib/qt5/plugins',
        ]
        for path in qt_plugin_paths:
            if path and os.path.exists(path):
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = path
                break

from PyQt5.QtWidgets import QApplication

if len(sys.argv) == 1:
    sys.stdout.flush()
    
    try:
        app = QApplication(sys.argv)
        sys.stdout.flush()
    except Exception as e:
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        app = QApplication(sys.argv)
    
    from ui import MainView
    
    window = MainView()
    window.show()
    sys.exit(app.exec())