import sys
import os

# Set matplotlib backend BEFORE any imports to prevent hanging
os.environ['MPLBACKEND'] = 'Qt5Agg'

# Ensure Qt platform plugin path is set correctly (especially on macOS)
# This prevents QApplication from hanging when trying to load plugins
if sys.platform == 'darwin':  # macOS
    # On macOS, use Cocoa platform explicitly
    if 'QT_QPA_PLATFORM' not in os.environ:
        os.environ['QT_QPA_PLATFORM'] = 'cocoa'
    
    # Try to find Qt plugins - check virtual environment first, then system locations
    if 'QT_QPA_PLATFORM_PLUGIN_PATH' not in os.environ:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)  # Go up one level from src/
        
        # Try to find PyQt5 plugins in virtual environment
        venv_plugin_path = None
        venv_lib = os.path.join(project_root, 'formula', 'lib')
        if os.path.exists(venv_lib):
            # Look for any python3.x directory
            for item in os.listdir(venv_lib):
                if item.startswith('python'):
                    potential_path = os.path.join(venv_lib, item, 'site-packages', 'PyQt5', 'Qt5', 'plugins')
                    if os.path.exists(potential_path):
                        venv_plugin_path = potential_path
                        break
        
        qt_plugin_paths = [
            # Check in virtual environment first
            venv_plugin_path,
            # Then check system locations
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
    # Create QApplication with explicit platform if needed
    # On macOS, sometimes Qt needs help finding the platform plugin
    print("Creating QApplication...")
    sys.stdout.flush()  # Ensure output is visible
    
    try:
        # Try creating QApplication with a timeout workaround
        # If it hangs, it's likely a display/plugin issue
        app = QApplication(sys.argv)
        print("QApplication created successfully")
        sys.stdout.flush()
    except Exception as e:
        print(f"Error creating QApplication: {e}")
        print("Trying with offscreen platform...")
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        app = QApplication(sys.argv)
    
    # Now import view after QApplication is created
    from view import MainView
    
    window = MainView()
    window.show()
    sys.exit(app.exec())
else:
    print("Usage: python3 main.py [opt:graph_type]")