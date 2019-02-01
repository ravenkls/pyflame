from widgets import PythonCodeEditor, CodeTabWidget
from PyQt5 import QtWidgets
import syntax
import sys
import os


class PyFlame(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.tab_widget = CodeTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.configure_menu()
        self.load_css(os.path.join('resources', 'css', 'dark_theme.css'))

    def load_css(self, path):
        with open(path) as css_file:
            self.setStyleSheet(css_file.read())

    def configure_menu(self):
        menu_structure = {
            'File': (
                ('New...', 'Ctrl+N', self.new_file),
                ('Open', 'Ctrl+O', self.open_file),
                ('Save', 'Ctrl+S', self.save_file),
                ('Save As...', None, self.save_as),
                (None, None, None),
                ('Settings', None, self.open_settings),
                ('Import Settings', None, self.import_settings),
                ('Export Settings', None, self.export_settings),
                (None, None, None),
                ('Exit', None, self.exit_program),
            ),
            'Edit': (
                ('Undo', 'Ctrl+Z', self.undo),
                ('Redo', 'Ctrl+Shift+Z', self.redo),
                (None, None, None),
                ('Cut', 'Ctrl+X', self.cut),
                ('Copy', 'Ctrl+C', self.copy),
                ('Paste', 'Ctrl+V', self.paste),
                (None, None, None),
                ('Style Code with PEP-8', 'Shift+Alt+F', self.style_code)
            )
        }
        for menu_name, menu_items in menu_structure.items():
            menu = self.menuBar().addMenu(menu_name)
            for item_name, shortcut, callback in menu_items:
                if item_name and shortcut:
                    menu.addAction(item_name, callback, shortcut)
                elif item_name:
                    menu.addAction(item_name, callback)
                else:
                    menu.addSeparator()

    # FILE MENU FUNCTIONS
    def new_file(self):
        pass

    def open_file(self):
        filename, filetype = QtWidgets.QFileDialog.getOpenFileName(self)
        if filename:
            with open(filename) as file:
                tab_name = os.path.basename(filename)
                code_widget = PythonCodeEditor(self)
                code_widget.setPlainText(file.read())
                index = self.tab_widget.addTab(code_widget, tab_name)
                self.tab_widget.setCurrentIndex(index)

    @property
    def code_widget(self):
        return self.tab_widget.currentWidget()

    def save_file(self):
        pass

    def save_as(self):
        pass

    def open_settings(self):
        pass

    def import_settings(self):
        pass

    def export_settings(self):
        pass

    def exit_program(self):
        pass

    # EDIT MENU FUNCTIONS
    def undo(self):
        self.code_widget.undo()

    def redo(self):
        self.code_widget.redo()

    def cut(self):
        self.code_widget.cut()

    def copy(self):
        self.code_widget.copy()

    def paste(self):
        self.code_widget.paste()

    def style_code(self):
        self.code_widget.autopep8_code()


