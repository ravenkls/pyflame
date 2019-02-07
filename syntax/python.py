# SYNTAX FOR PYTHON 3
from PyQt5.QtGui import QColor, QTextCharFormat
from PyQt5.QtCore import QRegExp

expressions = {
    'keywords': [QRegExp(r'\b' + x + r'\b') for x in [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'raise',
        'return', 'try', 'while', 'yield', 'with',
        'None', 'True', 'False', 'as'
    ]],

    'builtins': [QRegExp(r'\b' + x + r'\b') for x in [
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint',
        'bytearray', 'bytes', 'callable', 'chr', '@classmethod', 'compile',
        'complex', 'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval',
        'exec', 'filter', 'float', 'format', 'frozenset', 'getattr', 'globals',
        'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance', 'issubclass',
        'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview', 'min', 'next', 'object',
        'oct', 'open', 'ord', 'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round',
        'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple',
        'type', 'vars', 'zip', '__import__'
    ]],

    'comments': [QRegExp(x) for x in [
        r'#.*'
    ]],

    'numbers': [QRegExp(x) for x in [
        r'(?:[^\w]|^)\d+', # base 10 numbers
        r'(?:[^\w]|^)0x[0-9a-fA-F]+', # base 16 numbers
        r'(?:[^\w]|^)0b[0-1]+', # base 2 numbers
    ]],

    'strings': ["'", '"'],

    'operators': [QRegExp(x) for x in [
        '=', # assignment
        '==', '!=', '<', '<=', '>', '>=', # comparison
        '\+', '-', '\*', '/', '//', '\%', '\*\*', # arithmetic
        '\+=', '-=', '\*=', '/=', '\%=', # in place
        '\^', '\|', '\&', '\~', '>>', '<<', # bitwise
    ]],

    'braces': [QRegExp(x) for x in [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]],

    'function_names': [QRegExp(x) for x in [
        r'def[ \t]+(\w+)',
    ]],

    # Any other matches which don't fall into the above categories
    'custom_matches': [
        ('self', QRegExp(r'\bself\b')),
        ('class_names', QRegExp(r'class[ \t]+(\w+)'))
    ]
}

# Default width to indent at
indent_width = 4

# What line should trigger an indent on newline
indent_expressions = [
    # Functions
    QRegExp(r'def [\w]+\(*.*\)*:'),
    QRegExp(r'class [\w]+\(*.*\)*:'),
    # If statement
    QRegExp(r'if .+:'),
    QRegExp(r'elif:'),
    QRegExp(r'else:'),
    # With statement
    QRegExp(r'with .+:'),
    # Loops
    QRegExp(r'for .+:'),
    QRegExp(r'while .+:')
]

# Default colour scheme
theme = {
    'editor_background': QColor(0x282C34),
    'cursor_selection_colour': QColor(0x596470),
    'current_line_colour': QColor(0x2C3238),
    'margin_colour': QColor(0x515866),
    'line_numbers_colour': QColor(0x4f5766),
    'identifiers': QColor(0xA9B7C6),
    'keywords': QColor(0xC679DD),
    'builtins': QColor(0x57B6C2),
    'operators': QColor(0xA9B7C6),
    'braces': QColor(0xA9B7C6),
    'function_names': QColor(0x61AFEF),
    'class_names': QColor(0xFFC66D),
    'strings': QColor(0x98C476),
    'strings_unfinished': QColor(0x98C476),
    'multi_line_comments': QColor(0x98C476),
    'comments': QColor(0x808080),
    'numbers': QColor(0xD2945D),
    'self': QColor(0xE06C75),
}