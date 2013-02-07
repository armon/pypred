"""
This module provides the AST nodes that are used to
represent and later, evaluate a predicate.
"""

class Node(object):
    "Root object in the AST tree"
    def __init__(self):
        return

    def pre(self, func):
        """
        Performs a pre-order traversal of the
        tree, and invokes a callback for each node.
        """
        func(self)
        if hasattr(self, "left"):
            self.left.pre(func)
        if hasattr(self, "right"):
            self.right.pre(func)

    def __repr__(self):
        name = self.__class__.__name__
        r = name
        if hasattr(self, "type"):
            r += " t:" + str(self.type)
        if hasattr(self, "value"):
            r += " v:" + str(self.value)
        if hasattr(self, "left"):
            r += " l:" + self.left.__class__.__name__
        if hasattr(self, "right"):
            r += " r:" + self.right.__class__.__name__
        return r


class LogicalOperator(Node):
    "Used for the logical operators"
    def __init__(self, op, left, right):
        self.type = op
        self.left = left
        self.right = right

class NegateOperator(Node):
    "Used to negate a result"
    def __init__(self, expr):
        self.left = expr

class CompareOperator(Node):
    "Used for all the mathematical comparisons"
    def __init__(self, comparison, left, right):
        self.type = comparison
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
        # Unpack a Node object if we are given one
        if isinstance(value, Node):
            self.value = value.value
        else:
            self.value = value

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

