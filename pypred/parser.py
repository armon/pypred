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
    'DBL_EQUALS',
    'NOT_EQUALS',
    'IS_EQUALS',
    'IS_NOT_EQUALS',
    'LPAREN',
    'RPAREN',
    'LBRACK',
    'RBRACK',
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
t_DBL_EQUALS = r'=='
t_NOT_EQUALS = r'!='

t_LPAREN = r'\('
t_RPAREN = r'\)'

t_LBRACK = r'{'
t_RBRACK = r'}'

# Ignore any comments
t_ignore_COMMENT = r'\#.*'

def t_NUMBER(t):
    r'-?\d+(\.\d+)?'
    return t

# Matches either a sequence of non-whitespace
# or anything that is quoted
def t_STRING(t):
    r'([\w_\-.:;]+|"[^"]*"|\'[^\']*\')'
    l = t.value.lower()
    if l in reserved:
        t.value = l
    # Check for reserved words
    t.type = reserved.get(t.value, 'STRING')
    return t

# Track the newlines
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# The ignore characters
t_ignore = ' \t\n'

# Error handler
def t_error(t):
    if " " in t.value:
        idx = t.value.index(" ")
        error_loc = (t.value[:idx], t.lexer.lexpos, t.lexer.lineno)
        t.lexer.errors.append(error_loc)
        t.lexer.skip(idx)
    else:
        error_loc = (t.value, t.lexer.lexpos, t.lexer.lineno)
        t.lexer.errors.append(error_loc)
        t.lexer.skip(1)

# Build the lexer
def get_lexer():
    "Returns a new instance of the lexer"
    l = lex.lex()
    l.errors = []
    return l

###
# Implements the parser
###
import ply.yacc as yacc
from . import ast

precedence = (
    ('right', 'AND', 'OR'),
    ('right', 'NOT'),
)

def p_expression_binop(p):
    """expression : expression AND expression
                  | expression OR expression"""
    p[0] = ast.LogicalOperator(p[2], p[1], p[3])
    p[0].set_position(p.lineno(2), p.lexpos(2))

def p_expression_not(p):
    "expression : NOT expression"
    p[0] = ast.NegateOperator(p[2])
    p[0].set_position(p.lineno(1), p.lexpos(1))

def p_expression_term(p):
    "expression : term"
    p[0] = p[1]


def p_term_is_not(p):
    "term : factor IS_EQUALS NOT factor"
    p[0] = ast.CompareOperator("!=", p[1], p[4])
    p[0].set_position(p.lineno(2), p.lexpos(2))

def p_term_comparison(p):
    """term : factor GREATER_THAN factor
            | factor GREATER_THAN_EQUALS factor
            | factor LESS_THAN factor
            | factor LESS_THAN_EQUALS factor
            | factor EQUALS factor
            | factor NOT_EQUALS factor
            | factor IS_NOT_EQUALS factor
            | factor IS_EQUALS factor"""
    p[0] = ast.CompareOperator(p[2], p[1], p[3])
    p[0].set_position(p.lineno(2), p.lexpos(2))

def p_term_dbl_equals(p):
    "term : factor DBL_EQUALS factor"
    p[0] = ast.CompareOperator("=", p[1], p[3])
    p[0].set_position(p.lineno(2), p.lexpos(2))

def p_contains(p):
    "term : factor CONTAINS factor"
    p[0] = ast.ContainsOperator(p[1], p[3])
    p[0].set_position(p.lineno(2), p.lexpos(2))

def p_matchse(p):
    "term : factor MATCHES factor"
    p[0] = ast.MatchOperator(p[1], ast.Regex(p[3]))
    p[0].set_position(p.lineno(2), p.lexpos(2))

def p_term_factor(p):
    "term : factor"
    p[0] = p[1]


def p_factor_string(p):
    "factor : STRING"
    p[0] = ast.Literal(p[1])
    p[0].set_position(p.lineno(1), p.lexpos(1))

def p_factor_number(p):
    "factor : NUMBER"
    p[0] = ast.Number(p[1])
    p[0].set_position(p.lineno(1), p.lexpos(1))

def p_factor_constants(p):
    """factor : TRUE
              | FALSE
              | UNDEFINED
              | NULL
              | EMPTY"""
    if p[1] == "true":
        p[0] = ast.Constant(True)
        p[0].set_position(p.lineno(1), p.lexpos(1))
    elif p[1] == "false":
        p[0] = ast.Constant(False)
        p[0].set_position(p.lineno(1), p.lexpos(1))
    elif p[1] == "null":
        p[0] = ast.Constant(None)
        p[0].set_position(p.lineno(1), p.lexpos(1))
    elif p[1] == "undefined":
        p[0] = ast.Undefined()
        p[0].set_position(p.lineno(1), p.lexpos(1))
    elif p[1] == "empty":
        p[0] = ast.Empty()
        p[0].set_position(p.lineno(1), p.lexpos(1))
    else:
        raise SyntaxError

def p_factor_parens(p):
    "factor : LPAREN expression RPAREN"
    p[0] = p[2]

def p_empty(p):
    "empty : "
    pass

def p_factor_list(p):
    """factor_list : factor factor_list
                   | empty"""
    if len(p) == 2 and p[1] is None:
        p[0] = []
    else:
        p[0] = [p[1]] + p[2]

def p_factor_sets(p):
    "factor : LBRACK factor_list RBRACK"
    p[0] = ast.LiteralSet(p[2])

def p_error(p):
    "Handles errors"
    if p is None:
        raise SyntaxError("Unexpected end of predicate!")
    else:
        err = ("Syntax error at token", p.type, p.value, p.lexpos, p.lineno)
        parser = p.lexer.parser
        parser.errors.append(err)
        parser.errok()


def get_parser(lexer=None, debug=0):
    "Returns a new instance of the parser"
    p = yacc.yacc(debug=debug)
    p.errors = []
    if lexer:
        lexer.parser = p
        p.lexer = lexer
    return p

