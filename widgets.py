from PyQt5 import QtWidgets, QtGui, QtCore
from itertools import accumulate
from bidict import MutableBidict
from code import InteractiveConsole
from io import StringIO
import contextlib
import time
import autopep8
import syntax
import subprocess
import chardet
import re
import os


class RunConsoleDock(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        self.scroll_bar_at_bottom = False

        super().__init__('Run Console', parent)

        self.title_bar = QtWidgets.QWidget(self)
        self.title_bar.setObjectName('dock_title')
        title_layout = QtWidgets.QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)

        self.title_label = QtWidgets.QLabel('Run Console', self.title_bar)
        self.title_label.setObjectName('dock_title_label')
        size_policy = QtWidgets.QSizePolicy()
        size_policy.setHorizontalPolicy(QtWidgets.QSizePolicy.Expanding)
        self.title_label.setSizePolicy(size_policy)
        title_layout.addWidget(self.title_label)

        self.close_button = QtWidgets.QPushButton(self.title_bar)
        self.close_button.setObjectName('dock_close')
        self.close_button.clicked.connect(self.close)
        title_layout.addWidget(self.close_button)

        self.title_bar.setLayout(title_layout)
        self.setTitleBarWidget(self.title_bar)

        self.output_label = QtWidgets.QPlainTextEdit(self)
        self.output_label.setReadOnly(True)
        self.output_label.setObjectName('console')

        self.setWidget(self.output_label)

    def update_output(self, text):
        scroll_bar = self.output_label.verticalScrollBar()
        self.output_label.insertPlainText(text)
        if self.scroll_bar_at_bottom:
            self.output_label.verticalScrollBar().setValue(self.output_label.verticalScrollBar().maximum())
        if scroll_bar.value() == scroll_bar.maximum():
            self.scroll_bar_at_bottom = True
        else:
            self.scroll_bar_at_bottom = False

    def run_script(self, file):
        self.script_thread = RunScriptThread(file)
        self.script_thread.stdout.connect(self.update_output)
        self.script_thread.finished_stdout.connect(self.output_label.setPlainText)
        self.script_thread.start()


class RunScriptThread(QtCore.QThread):

    stdout = QtCore.pyqtSignal(str)
    finished_stdout = QtCore.pyqtSignal(str)

    def __init__(self, file):
        super().__init__()
        self.file = file
        self.total_stdout = f'Executing {file}...\n'
        self.next_stdout = self.total_stdout

    def run(self):
        self.finished_stdout.emit(self.next_stdout)
        start_time = time.time()
        process = subprocess.Popen('python "' + self.file + '"', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        emits = 0
        while process.poll() is None:
            next_line = process.stdout.readline()
            self.total_stdout += next_line.decode()
            self.next_stdout += next_line.decode()
            if round(time.time() - start_time, 1) > emits * 0.2:
                self.stdout.emit(self.next_stdout)
                self.next_stdout = ''
                emits += 1
        time_taken = time.time() - start_time
        cleanup, errors = process.communicate()
        final_string = self.total_stdout + cleanup.decode()
        if errors:
            final_string += '\n' + errors.decode() + '\n'
        self.finished_stdout.emit(final_string + '\nTime Elapsed: {}s\n'.format(round(time_taken, 5)))


class ProjectStructureDock(QtWidgets.QDockWidget):

    file_opened = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__('Project Structure', parent)

        self.title_bar = QtWidgets.QWidget(self)
        self.title_bar.setObjectName('dock_title')
        title_layout = QtWidgets.QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)

        self.title_label = QtWidgets.QLabel('Project Structure', self.title_bar)
        self.title_label.setObjectName('dock_title_label')
        size_policy = QtWidgets.QSizePolicy()
        size_policy.setHorizontalPolicy(QtWidgets.QSizePolicy.Expanding)
        self.title_label.setSizePolicy(size_policy)
        title_layout.addWidget(self.title_label)

        self.close_button = QtWidgets.QPushButton(self.title_bar)
        self.close_button.setObjectName('dock_close')
        self.close_button.clicked.connect(self.close)
        title_layout.addWidget(self.close_button)

        self.title_bar.setLayout(title_layout)
        self.setTitleBarWidget(self.title_bar)
        self.init_project_structure_widget()
        self.dockLocationChanged.connect(self.style_borders)

    def style_borders(self, location):
        primary_colour = self.parent().primary_colour.name()
        secondary_colour = self.parent().secondary_colour.name()
        self.title_label.setStyleSheet(f'QLabel#dock_title_label{{border-bottom: 1px solid {secondary_colour};}}')
        self.title_bar.setStyleSheet(f'QWidget#dock_title{{border-bottom: 1px solid {secondary_colour};}}')

    def reload_directory(self):
        self.project_structure_tree.setRootIndex(self.filesystem_model.setRootPath(os.getcwd()))

    def init_project_structure_widget(self):
        self.filesystem_model = QtWidgets.QFileSystemModel()
        self.filesystem_model.setFilter(QtCore.QDir.AllEntries | QtCore.QDir.NoDotAndDotDot)
        self.project_structure_tree = QtWidgets.QTreeView(self)
        self.project_structure_tree.setModel(self.filesystem_model)
        self.project_structure_tree.hideColumn(1) # Size Column
        self.project_structure_tree.hideColumn(2) # Type Column
        self.project_structure_tree.hideColumn(3) # Date Modified Column
        self.project_structure_tree.setObjectName('project_structure')
        self.project_structure_tree.setHeaderHidden(True)
        self.project_structure_tree.activated.connect(self.item_clicked)
        self.setWidget(self.project_structure_tree)
        self.reload_directory()

    def item_clicked(self, index):
        path = str(self.filesystem_model.filePath(index))
        if os.path.isfile(path):
            self.file_opened.emit(path)



class CodeTabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('code_tabs')
        self.open_editors = MutableBidict()
        self.welcome_tab = self.show_welcome_tab()
        self.setTabsClosable(True)
        self.setMovable(True)

    def addTab(self, path):
        read_only = False
        if os.path.exists(path):
            with open(path, 'rb') as file:
                try:
                    file_bytes = file.read()
                    encoding = chardet.detect(file_bytes)['encoding']
                    contents = file_bytes.decode(encoding)
                except UnicodeDecodeError:
                    contents = str(file_bytes)[2:-2]
                    read_only = True
        else:
            with open(path, 'w') as file:
                contents = ''

        tab_name = os.path.basename(path)
        if not self.open_editors.get(path):
            code_widget = PythonCodeEditor(self)
            code_widget.setReadOnly(read_only)
            code_widget.setPlainText(contents)
            code_widget.setFocus()
            self.open_editors[path] = code_widget
            super().addTab(self.open_editors[path], tab_name)

        if self.welcome_tab is not None:
            super().removeTab(self.welcome_tab)
            self.welcome_tab = None

        return self.open_editors[path]

    def removeTab(self, p_int):
        widget = self.widget(p_int)
        self.open_editors.inv.pop(widget)
        super().removeTab(p_int)
        if self.tabBar().count() < 1:
            self.welcome_tab = self.show_welcome_tab()

    def show_welcome_tab(self):
        code_widget = PythonCodeEditor(self)
        code_widget.setPlainText('import webbrowser\n'
                                 '\n\n'
                                 '# Welcome To PyFlame\n'
                                 '# Made by Kristian Smith\n\n\n'
                                 'GITHUB_URL = \'https://www.github.com/ravenkls\'\n'
                                 'REDDIT_URL = \'https://www.reddit.com/user/raaaaavenn\'\n'
                                 'DONATE_URL = \'https://www.paypal.me/kristian01\'\n\n\n'
                                 'if input(\'Start new project? \').lower() == \'y\':\n'
                                 '    pyflame = PyFlame()\n'
                                 '    pyflame.start_project()\n'
                                 '    print(\'Yay!\')\n'
                                 'else:\n'
                                 '    print(\'Okay, check out my GitHub instead!\')\n'
                                 '    webbrowser.open(GITHUB_URL)\n')
        code_widget.setReadOnly(True)
        index = super().addTab(code_widget, 'welcome.py')
        button = QtWidgets.QPushButton()
        button.setStyleSheet('width: 0px; padding: 0px; margin: 0px; background: transparent;')
        self.tabBar().setTabButton(index, QtWidgets.QTabBar.RightSide, button)
        return index

class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QtGui.QSize(self.editor.line_numbers_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)

class CodeEditor(QtWidgets.QPlainTextEdit):
    def __init__(self, language, parent=None):
        super().__init__(parent)
        self.font_size = 12

        # General
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.selectionChanged.connect(self.highlight_similar_words)

        # Line Numbers
        self.language = language
        self.theme = language.theme
        self.line_numbers_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_numbers_area_width)
        self.updateRequest.connect(self.update_line_numbers_area)
        self.update_line_numbers_area_width(0)

        # Syntax Theme
        self.font_family_id = QtGui.QFontDatabase.addApplicationFont(os.path.join('resources', 'fonts' 'FiraCode.ttf'))
        try:
            self.font_family = QtGui.QFontDatabase.applicationFontFamilies(self.font_family_id)[0]
        except IndexError:
            self.font_family = 'Consolas'
        self.set_highlighter(syntax.Highlighter)
        font = QtGui.QFont()
        font.setPointSize(self.font_size)
        font.setFamily(self.font_family)
        self.setFont(font)
        self.activate_theme()

    def set_highlighter(self, highlighter_class):
        self.highlighter = highlighter_class(self.language, self.document())

    def highlight_similar_words(self):
        plaintext = self.toPlainText()
        selection_start = self.textCursor().selectionStart()
        selection_end = self.textCursor().selectionEnd()
        selection_word = plaintext[selection_start:selection_end]
        if not selection_word:
            return self.setExtraSelections([])
        if selection_start != 0:
            selection_start -= 1
        if selection_end != len(plaintext):
            selection_end += 1
        selection_context = plaintext[selection_start:selection_end]
        regexp = QtCore.QRegExp(rf'\b{re.escape(selection_word)}\b')
        if regexp.indexIn(selection_context, 0) >= 0:
            index = regexp.indexIn(plaintext, 0)
            extra_selections = []
            while index >= 0:
                length = regexp.matchedLength()
                selection = QtWidgets.QTextEdit.ExtraSelection()

                selection.format.setBackground(self.theme['cursor_selection_colour'])
                selection.format.setForeground(QtGui.QColor(0xFFFFFF))
                selection.cursor = self.textCursor()
                selection.cursor.setPosition(index)
                selection.cursor.setPosition(index + length, QtGui.QTextCursor.KeepAnchor)
                extra_selections.append(selection)
                index = regexp.indexIn(plaintext, index+length)
            self.setExtraSelections(extra_selections)


    def activate_theme(self):
        '''Change the current theme'''
        background_colour = self.theme['editor_background'].name()
        identifiers_colour = self.theme['identifiers'].name()
        selection_colour = self.theme['cursor_selection_colour'].name()
        self.setStyleSheet(f'background: {background_colour};'
                           f'color: {identifiers_colour};'
                           f'selection-background-color: {selection_colour};'
                           'border: none;')

    def line_numbers_area_width(self):
        '''Get the calcuated width of the line number area'''
        max_value = self.blockCount() or 1
        space = self.fontMetrics().width(str(max_value)) + 30
        return space

    def update_line_numbers_area_width(self, width):
        '''Set margin for line numbers'''
        self.setViewportMargins(self.line_numbers_area_width()+5, 0, 0, 0)

    def update_line_numbers_area(self, rect, dy):
        if dy:
            self.line_numbers_area.scroll(0, dy)
        else:
            self.line_numbers_area.update(0, rect.y(), self.line_numbers_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_numbers_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_numbers_area.setGeometry(QtCore.QRect(cr.left(), cr.top(), self.line_numbers_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QtGui.QPainter(self.line_numbers_area)
        painter.fillRect(event.rect(), self.theme['editor_background'].lighter(105))
        block = self.firstVisibleBlock()
        total_lines = self.blockCount()
        font = QtGui.QFont(self.font_family)
        font.setPointSize(self.font_size)
        painter.setFont(font)

        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                if blockNumber == self.textCursor().block().blockNumber():
                    painter.setPen(self.theme['line_numbers_colour'].lighter(150))
                    painter.fillRect(0, top, self.line_numbers_area_width(), height, self.theme['editor_background'].lighter(140))
                else:
                    painter.setPen(self.theme['line_numbers_colour'])
                left_padding = self.fontMetrics().width(str(total_lines)) + 15
                painter.drawText(0, top, left_padding, height, QtCore.Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1


class AutoIndentCodeEditor(CodeEditor):
    def __init__(self, language, parent=None):
        super().__init__(language, parent)

    @property
    def control_modifier(self):
        return QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier

    @property
    def shift_modifier(self):
        return QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier

    def wheelEvent(self, event):
        if self.control_modifier:
            if event.angleDelta().y() > 0 and self.font_size < 32:
                self.font_size += 1
            elif event.angleDelta().y() < 0 and self.font_size > 1:
                self.font_size -= 1
            font = self.font()
            font.setPointSize(self.font_size)
            self.setFont(font)
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.newline(event)
        elif event.key() == QtCore.Qt.Key_Backspace:
            self.backspace(event)
        elif event.key() == QtCore.Qt.Key_Tab:
            self.indent(self.language.indent_width)
        else:
            super().keyPressEvent(event)


    def autopep8_code(self):
        cursor = self.textCursor()
        position = self.textCursor().position()
        scrollbar = self.verticalScrollBar().value()

        cursor.select(cursor.Document)
        cursor.insertText(autopep8.fix_code(self.toPlainText(), options={'ignore': ['E501']}))
        cursor.setPosition(position)

        self.setTextCursor(cursor)
        self.verticalScrollBar().setValue(scrollbar)

    def newline(self, event):
        '''Creates a newline, aware of current indentation'''
        current_line = str(self.textCursor().block().text())
        indent_width = len(current_line) - len(current_line.lstrip())

        for regex in self.language.indent_expressions:
            if regex.indexIn(current_line, 0) >= 0:
                indent_width += self.language.indent_width

        current_position = self.textCursor().position()
        super().keyPressEvent(event)
        self.indent(indent_width)

    def unindent(self, amount, block_number=None):
        '''Indents the current line by a specified amount'''
        if not block_number:
            block_number = self.textCursor().block().blockNumber()
        current_position = self.textCursor().block()
        for _ in range(amount):
            self.textCursor().deletePreviousChar()

    def indent(self, amount, block_number=None):
        '''Indents the current line by a specified amount'''
        if not block_number:
            block_number = self.textCursor().block().blockNumber()
        self.insertPlainText(' '*amount)

    def backspace(self, event):
        current_cursor = self.textCursor()
        current_line = str(current_cursor.block().text())
        indent_width = len(current_line) - len(current_line.lstrip())
        chars_behind_cursor = current_cursor.position() - current_cursor.block().position()

        if chars_behind_cursor <= indent_width and indent_width != 0:
            remove_amount = chars_behind_cursor % self.language.indent_width or self.language.indent_width
            self.unindent(remove_amount)
        else:
            super().keyPressEvent(event)


class PythonCodeEditor(AutoIndentCodeEditor):
    def __init__(self, parent=None):
        super().__init__(syntax.python, parent)
        self.set_highlighter(syntax.PythonHighlighter)