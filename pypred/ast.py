"""
This module provides the AST nodes that are used to
represent and later, evaluate a predicate.
"""

class Node(object):
    "Root object in the AST tree"
    def __init__(self):
        return

class LogicalOperator(Node):
    "Used for the logical operators"
    def __init__(self, op, left, right):
        self.operator = op
        self.left = left
        self.right = right

class CompareOperator(Node):
    "Used for all the mathematical comparisons"
    def __init__(self, comparison, left, right):
        self.comparison = comparison
        self.left = left
        self.right = right

class ContainsOperator(Node):
    "Used for the 'contains' operator"
    def __init__(self, left, right):
        self.left = left
        self.right = right

class MatchOperator(Node):
    "Used for the 'matches' operator"
    def __init__(self, left, right):
        self.left = left
        self.right = right

class Regex(Node):
    "Regular expression literal"
    def __init__(self, value):
        self.re_str = value

class Literal(Node):
    "String literal"
    def __init__(self, value):
        self.value = value

class Number(Node):
    "Numeric literal"
    def __init__(self, value):
        self.value = value

class Constant(Node):
    "Used for true, false, null"
    def __init__(self, value):
        self.value = value

class Undefined(Node):
    "Represents a non-defined object"
    def __init__(self):
        return

def Empty(Node):
    "Represents the null set"
    def __init__(self):
        return

