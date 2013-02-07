"""
This module makes use of the Python PLY package
to parse the grammars
"""
###
# Implements the lexer
###
import ply.lex as lex

reserved = {
    'is': 'IS_EQUALS',
    'and': 'AND',
    'or': 'OR',
    'not': 'NOT',
    'contains': 'CONTAINS',
    'matches': 'MATCHES',
    'true': 'TRUE',
    'false': 'FALSE',
    'undefined': 'UNDEFINED',
    'null': 'NULL',
    'empty': 'EMPTY'
}

tokens = (
    'AND',
    'OR',
    'NOT',
    'GREATER_THAN',
    'GREATER_THAN_EQUALS',
    'LESS_THAN',
    'LESS_THAN_EQUALS',
    'EQUALS',
    'NOT_EQUALS',
    'IS_EQUALS',
    'IS_NOT_EQUALS',
    'LPAREN',
    'RPAREN',
    'CONTAINS',
    'MATCHES',
    'NUMBER',
    'STRING',
    'TRUE',
    'FALSE',
    'UNDEFINED',
    'NULL',
    'EMPTY'
)

# Regex rules for tokens
t_GREATER_THAN = r'>'
t_GREATER_THAN_EQUALS = r'>='

t_LESS_THAN = r'<'
t_LESS_THAN_EQUALS = r'<='

t_EQUALS = r'='
t_NOT_EQUALS = r'!='

t_LPAREN = r'\('
t_RPAREN = r'\)'

# Ignore any comments
t_ignore_COMMENT = r'\#.*'

def t_NUMBER(t):
    r'-?\d+(\.\d+)?'
    t.value = float(t.value)
    return t

# Matches either a sequence of non-whitespace
# or anything that is quoted
def t_STRING(t):
    r'([\w_\-.:;]+|"[^"]*"|\'[^\']*\')'
    # Check for reserved words
    t.type = reserved.get(t.value,'STRING')
    return t

# Track the newlines
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# The ignore characters
t_ignore = ' \t\n'

# Error handler
def t_error(t):
    error_loc = (t.value, t.lexer.lexpos, t.lexer.lineno)
    t.lexer.errors.append(error_loc)
    t.lexer.skip(1)

# Build the lexer
def get_lexer():
    "Returns a new instance of the lexer"
    return lex.lex()

###
# Implements the parser
###
import ply.yacc as yacc



def get_parser():
    "Returns a new instance of the parser"
    return yacc.yacc()

