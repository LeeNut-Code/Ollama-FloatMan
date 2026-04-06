import sys
from PyQt5.QtWidgets import QApplication
from app import OllamaManagerApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OllamaManagerApp()
    window.show()
    sys.exit(app.exec_())
