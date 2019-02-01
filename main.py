from PyQt5 import QtWidgets
from editor import PyFlame
import sys

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ide = PyFlame()
    ide.resize(1280, 720)
    ide.show()
    sys.exit(app.exec_())