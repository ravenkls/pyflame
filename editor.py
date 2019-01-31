from widgets import PythonCodeEditor
from PyQt5 import QtWidgets
import syntax
import sys


app = QtWidgets.QApplication(sys.argv)

window = QtWidgets.QMainWindow()


def open_file():
    file, filetype = QtWidgets.QFileDialog.getOpenFileName(window)
    with open(file) as file:
        code_widget.setPlainText(file.read())


def save_file():
    pass


code_widget = PythonCodeEditor(syntax.python, parent=window)
code_widget.resize(640, 480)
window.setCentralWidget(code_widget)

menu_bar = window.menuBar()
file_menu = menu_bar.addMenu('File')
file_menu.addAction('Open', open_file)
file_menu.addAction('Save As', save_file)

window.show()
sys.exit(app.exec_())