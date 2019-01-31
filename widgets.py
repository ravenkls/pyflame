from PyQt5 import QtWidgets, QtGui, QtCore
from itertools import accumulate
import autopep8
import syntax
import re

def qcolor_to_string(qcolor):
    r, g, b, a = qcolor.red(), qcolor.green(), qcolor.blue(), qcolor.alpha()
    return f'rgba({r}, {g}, {b}, {a})'

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
        self.font_family_id = QtGui.QFontDatabase.addApplicationFont('resources/fonts/FiraCode.ttf')
        self.font_family = QtGui.QFontDatabase.applicationFontFamilies(self.font_family_id)[0]
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
        regexp = QtCore.QRegExp(rf'\b{selection_word}\b')
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
        background_colour = qcolor_to_string(self.theme['editor_background'])
        identifiers_colour = qcolor_to_string(self.theme['identifiers'])
        selection_colour = qcolor_to_string(self.theme['cursor_selection_colour'])
        self.setStyleSheet(f'background: {background_colour};'
                           f'color: {identifiers_colour};'
                           f'selection-background-color: {selection_colour};')

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
        self.control_modifier = False
        self.shift_modifier = False

    def keyPressEvent(self, event):
        self.scroll_bar_position = self.verticalScrollBar().value()

        if event.key() == QtCore.Qt.Key_Control:
            self.control_modifier = True
        elif event.key() == QtCore.Qt.Key_Shift:
            self.shift_modifier = True

        if event.key() == QtCore.Qt.Key_Return:
            self.newline(event)
        elif event.key() == QtCore.Qt.Key_Backspace:
            self.backspace(event)
        elif event.key() == QtCore.Qt.Key_Tab:
            self.indent(self.language.indent_width)
        elif event.key() == QtCore.Qt.Key_S and self.control_modifier:
            self.save_code()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Control:
            self.control_modifier = False
        elif event.key() == QtCore.Qt.Key_Shift:
            self.shift_modifier = False

        super().keyReleaseEvent(event)

    def save_code(self):
        cursor = self.textCursor()
        position = self.textCursor().position()
        scrollbar = self.verticalScrollBar().value()

        cursor.select(cursor.Document)
        cursor.insertText(autopep8.fix_code(self.toPlainText()))
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
    def __init__(self, language, parent=None):
        super().__init__(language, parent)
        self.set_highlighter(syntax.PythonHighlighter)