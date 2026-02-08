import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow


def main():
    # PyQt6 handles High DPI automatically by default.
    # We removed the manual attributes that caused the crash.
    
    try:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon("logo.png"))
        app.setStyle("Fusion")
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
        
    except Exception as e:
        # Show detailed error information
        from util.logger import logger
        logger.critical("FATAL ERROR DETECTED", exc_info=True)
        
        # Try to show error dialog (may fail if QApplication wasn't created)
        try:
            QMessageBox.critical(None, "Fatal Error", 
                f"Failed to start application:\n\n{type(e).__name__}: {str(e)}\n\nSee console for details.")
        except:
            pass
        
        sys.exit(1)

if __name__ == '__main__':
    main()
