from PyQt5 import QtWidgets, QtCore
from editor import PyFlame
import resources
import sys

themes = {
    'FOREST': '#364c30',
    'NIGHT': '#30384c',
    'ROYAL': '#35304c'
}

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    settings = QtCore.QSettings('ravenkls', 'PyFlame')
    ide = PyFlame(settings, primary_colour=themes['NIGHT'])
    sys.exit(app.exec_())
