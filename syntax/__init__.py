from PyQt5.QtGui import QSyntaxHighlighter
from PyQt5.QtCore import QRegExp
import re
from . import python

class Highlighter(QSyntaxHighlighter):

    NORMAL_STATE = 0
    MULTILINE_STRING_STATE = 1

    def __init__(self, language, document):
        super().__init__(document)
        self.theme = language.theme
        self.current_string_delimiter = None
        self.normal_expressions = dict(language.expressions)
        self.string_delimiters = self.normal_expressions.pop('strings')
        self.custom_expressions = self.normal_expressions.pop('custom_matches')
        self.comment_expressions = self.normal_expressions.pop('comments')

    def highlightBlock(self, text):
        self.setCurrentBlockState(self.NORMAL_STATE)

        text = self.match_comments(text)

        for expression_type, regex_list in self.normal_expressions.items():
            for regex in regex_list:
                index = regex.indexIn(text, 0) # get the index of the first match
                while index >= 0:
                    nth = 1 if regex.pos(1) >= 0 else 0 # get the match, prefer a group match, if not get all of it
                    index = regex.pos(nth)
                    length = len(regex.cap(nth))
                    self.setFormat(index, length, self.theme[expression_type])
                    index = regex.indexIn(text, index + length)

        for expression_type, regex in self.custom_expressions:
            index = regex.indexIn(text, 0)  # get the index of the first match
            while index >= 0:
                nth = 1 if regex.pos(1) >= 0 else 0  # get the match, prefer a group match, if not get all of it
                index = regex.pos(nth)
                length = len(regex.cap(nth))
                self.setFormat(index, length, self.theme[expression_type])
                index = regex.indexIn(text, index + length)

        string_indexes = self.match_full_strings(text)
        for index, length in string_indexes:
            self.setFormat(index, length, self.theme['strings'])

    def match_comments(self, text):
        comment_indexes = []
        for regex in self.comment_expressions:
            index = regex.indexIn(text, 0)  # get the index of the first match
            while index >= 0:
                comment_indexes.append(index)
                nth = 1 if regex.pos(1) >= 0 else 0  # get the match, prefer a group match, if not get all of it
                index = regex.pos(nth)
                length = len(regex.cap(nth))
                self.setFormat(index, length, self.theme['comments'])
                index = regex.indexIn(text, index + length)

                self.setCurrentBlockState(self.NORMAL_STATE)
                if comment_indexes:
                    text = text[:min(comment_indexes)]
        return text

    def match_full_strings(self, text):
        string_indexes = []
        start_string_index = None
        end_string_index = None
        last_last_letter = ''
        last_letter = ''

        current_string = self.previousBlockState() == self.MULTILINE_STRING_STATE
        if current_string:
            start_string_index = 0

        for i, letter in enumerate(text):
            try:
                delimiter = self.string_delimiters.index(letter) + 1
            except ValueError:
                delimiter = None
            if current_string:
                if delimiter and (last_letter != '\\' or (last_letter == '\\' and last_last_letter == '\\')):
                    if letter == self.current_string_delimiter:
                        current_string = False
                    string_indexes.append((start_string_index, i - start_string_index + 1))
                elif string_indexes:
                    string_indexes[-1] = (start_string_index, i-start_string_index + 1)
                else:
                    string_indexes = [(start_string_index, i-start_string_index + 1)]
            elif delimiter:
                self.current_string_delimiter = letter
                current_string = True
                start_string_index = i
                string_indexes.append((start_string_index, i-start_string_index + 1))

            if last_letter:
                last_last_letter, last_letter = last_letter, letter
            else:
                last_letter = letter

        if len(text) > 2 and current_string:
            if text[-1] == '\\' and text[-2] != '\\':
                self.setCurrentBlockState(self.MULTILINE_STRING_STATE)

        return string_indexes


class PythonHighlighter(Highlighter):

    TRIPLE_QUOTE_STRING_STATE = 2
    LINE_COMMENT_STATE = 3

    def match_multiline_strings(self, text):
        multiline_indexes = []
        current_string = self.previousBlockState() == self.TRIPLE_QUOTE_STRING_STATE
        if current_string:
            start_string_index = 0
            end_string_index = 0
        else:
            start_string_index = None
            end_string_index = None
        string_trigger = False

        for i, letter in enumerate(text):
            if i >= 2:
                last_3_letters = text[i-2:i+1]
                if last_3_letters == '"""' or last_3_letters == "'''":
                    string_trigger = True

            if i >= 3 and string_trigger:
                last_4_letters = text[i-3:i+1]
                if last_4_letters in ('\\"""', "\\'''"):
                    string_trigger = False
                    if i >= 4:
                        last_5_letters = text[i-4:i+1]
                        if last_5_letters == '\\\\"""' or last_5_letters == "\\\\'''":
                            string_trigger = True

            if not current_string and string_trigger:
                start_string_index = i
                current_string = True
                string_trigger = False
                multiline_indexes.append((start_string_index, i-start_string_index+2))
            elif current_string and string_trigger:
                current_string = False
                string_trigger = False
            elif current_string and multiline_indexes:
                multiline_indexes[-1] = (start_string_index, i - start_string_index + 2)
            elif current_string:
                multiline_indexes.append((start_string_index, i - start_string_index + 2))

        if current_string:
            self.setCurrentBlockState(self.TRIPLE_QUOTE_STRING_STATE)

        return multiline_indexes

    def match_full_strings(self, text):
        string_indexes = []
        start_string_index = None
        end_string_index = None
        last_last_letter = ''
        last_letter = ''

        current_string = self.previousBlockState() == self.MULTILINE_STRING_STATE
        if current_string:
            start_string_index = 0

        for i, letter in enumerate(text):
            try:
                delimiter = self.string_delimiters.index(letter) + 1
            except ValueError:
                delimiter = None
            if current_string:
                if delimiter and (last_letter != '\\' or (last_letter == '\\' and last_last_letter == '\\')):
                    if letter == self.current_string_delimiter:
                        current_string = False
                    string_indexes.append((start_string_index, i - start_string_index + 1))
                elif string_indexes:
                    string_indexes[-1] = (start_string_index, i-start_string_index + 1)
                else:
                    string_indexes = [(start_string_index, i-start_string_index + 1)]
            elif delimiter and letter + last_last_letter + last_last_letter not in ("'''", '"""'):
                self.current_string_delimiter = letter
                current_string = True
                start_string_index = i
                string_indexes.append((start_string_index, i-start_string_index + 1))

            if last_letter:
                last_last_letter, last_letter = last_letter, letter
            else:
                last_letter = letter

        if len(text) > 2 and current_string:
            if text[-1] == '\\' and text[-2] != '\\':
                self.setCurrentBlockState(self.MULTILINE_STRING_STATE)

        return string_indexes

    def match_comments(self, text):
        multiline_indexes = self.match_multiline_strings(text)
        comment_indexes = []
        for regex in self.comment_expressions:
            index = regex.indexIn(text, 0)  # get the index of the first match
            while index >= 0:
                nth = 1 if regex.pos(1) >= 0 else 0  # get the match, prefer a group match, if not get all of it
                index = regex.pos(nth)
                length = len(regex.cap(nth))
                if all(index > i+l for i, l in multiline_indexes if i == 0):
                    comment_indexes.append(index)
                    self.setFormat(index, length, self.theme['comments'])
                    self.setCurrentBlockState(self.NORMAL_STATE)
                index = regex.indexIn(text, index + length)
                if comment_indexes:
                    text = text[:min(comment_indexes)]

        # Match multi-line strings
        multiline_indexes = self.match_multiline_strings(text)
        for index, length in multiline_indexes:
            self.setFormat(index, length, self.theme['strings'])

        return text