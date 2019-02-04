from widgets import PythonCodeEditor, CodeTabWidget, ProjectStructureDock, RunConsoleDock
from PyQt5 import QtWidgets, QtCore, QtGui
import syntax
import sys
import os

class PyFlame(QtWidgets.QMainWindow):

    def __init__(self, primary_colour='#000000'):
        super().__init__()
        self.modal_dialog = None

        # Colours
        self.primary_colour = QtGui.QColor(primary_colour)
        self.secondary_colour = self.primary_colour.lighter(180)
        self.stylesheet = os.path.join('resources', 'css', 'dark_theme.css')
        self.load_css(self.stylesheet)

        # Code Area
        self.tab_widget = CodeTabWidget()
        self.tab_widget.tabCloseRequested.connect(self.close_editor_tab)

        # Project Folder Area
        self.project_structure = ProjectStructureDock(self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.project_structure)
        self.project_structure.file_opened.connect(self.new_editor_tab)

        # Run Console Area
        self.run_console = RunConsoleDock(self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.run_console)

        self.setCentralWidget(self.tab_widget)
        self.configure_menu()
        self.setMinimumSize(640, 480)
        self.tabs_metadata = {}
        self.files_open = []

    def load_css(self, path):
        with open(path) as css_file:
            css = css_file.read().replace('%PRIMARY%', self.primary_colour.name())
            css = css.replace('%SECONDARY%', self.secondary_colour.name())
            css = css.replace('%HIGHLIGHTED%', self.primary_colour.lighter(150).name())
            css = css.replace('%HOVER%', self.primary_colour.lighter(125).name())
            self.setStyleSheet(css)

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

    def resizeEvent(self, event):
        if self.modal_dialog:
            self.modal_dialog.move(self.rect().center().x() - self.modal_dialog.width() // 2,
                                   self.rect().center().y() - self.modal_dialog.height() // 2)

    def new_editor_tab(self, path):
        widget = self.tab_widget.addTab(path)
        self.tab_widget.setCurrentWidget(widget)

    def close_editor_tab(self, tab_index):
        self.tab_widget.removeTab(tab_index)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape and self.modal_dialog:
            if self.modal_dialog.isVisible():
                self.modal_dialog.close()
        elif event.key() == QtCore.Qt.Key_F5:
            try:
                path = self.tab_widget.open_editors.inv[self.tab_widget.currentWidget()]
                self.run_console.run_script(path)
            except KeyError:
                pass

    # FILE MENU FUNCTIONS
    def new_file(self):
        self.modal_dialog = QtWidgets.QWidget(self)
        self.modal_dialog.setObjectName('modal')
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(8)
        layout.setAlignment(QtCore.Qt.AlignVCenter)

        title_label = QtWidgets.QLabel('New File...')
        title_label.setObjectName('header')
        layout.addWidget(title_label)

        file_name_entry = QtWidgets.QLineEdit()
        file_name_entry.setObjectName('dialog_entry')
        file_name_entry.setPlaceholderText('Enter New Filename')
        file_name_entry.returnPressed.connect(lambda: self.create_new_file(file_name_entry.text()))
        layout.addWidget(file_name_entry)

        self.modal_dialog.setLayout(layout)
        self.modal_dialog.show()
        file_name_entry.setFocus()
        self.modal_dialog.resize(self.width(), 75)
        self.modal_dialog.move(0, self.height() - self.modal_dialog.height())

    def create_new_file(self, path):
        if os.path.exists(path):
            print('File Already Exists')
        else:
            self.new_editor_tab(path)
        self.modal_dialog.close()

    def open_file(self):
        filename, filetype = QtWidgets.QFileDialog.getOpenFileName(self)
        if filename:
            self.new_editor_tab(filename)

    @property
    def code_widget(self):
        if not self.tab_widget.welcome_tab:
            return self.tab_widget.currentWidget()

    @property
    def code_widget_path(self):
        return self.tab_widget.open_editors.inv.get(self.code_widget)

    def save_file(self):
        if self.code_widget_path:
            with open(self.code_widget_path, 'w') as file:
                file.write(self.code_widget.toPlainText())

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


