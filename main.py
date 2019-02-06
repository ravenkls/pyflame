from PyQt5 import QtWidgets, QtCore
from editor import PyFlame
import sys

themes = {
    'RED': '#4c3030',
    'ORANGE': '#4c3d30',
    'YELLOW': '#4b4c30',
    'GREEN': '#364c30',
    'BLUE': '#30384c',
    'PURPLE': '#35304c',
    'PINK': '#4c3046',
}

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    settings = QtCore.QSettings('ravenkls', 'PyFlame')
    ide = PyFlame(settings, primary_colour=themes['BLUE'])
    sys.exit(app.exec_())