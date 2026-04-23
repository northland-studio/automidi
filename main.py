import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    
    app.setApplicationName("AutoMidi")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("NorthlandStudio")
    
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
