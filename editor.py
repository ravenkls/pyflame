from widgets import PythonCodeEditor
from PyQt5 import QtWidgets
import syntax
import sys

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    code_widget = PythonCodeEditor(syntax.python)
    code_widget.resize(640, 480)
    code_widget.show()
    sys.exit(app.exec_())