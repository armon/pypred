"""
This module helps with 'tiling' which is the process
of pattern matching against AST trees. This can be
used either for optimizations by re-writing the
AST tree, or for things like expression counting and
merging.
"""

class Pattern(object):
    "Base class for patterns. Always matches"
    def matches(self, node):
        "Returns if the current node matches the pattern"
        return True

class ASTPattern(Pattern):
    "Implements AST based pattern"
    def __init__(self, ast):
        self.ast = ast

    def matches(self, node):
        "Returns if the current node matches the ast"
        return self.compare_nodes(self.ast, node)

    @classmethod
    def compare_nodes(cls, a, b):
        if a.__class__ != b.__class__:
            return False
        if hasattr(a, "value") and a.value != b.value:
            return False
        if hasattr(a, "type") and a.type != b.type:
            return False
        if hasattr(a, "left") and \
            not cls.compare_nodes(a.left, b.left):
            return False
        if hasattr(b, "right") and \
            not cls.compare_nodes(a.right, b.right):
            return False
        return True

class SimplePattern(Pattern):
    "Implements a simple DSL for patterns"
    def __init__(self, node_p, left_p=None, right_p=None):
        """
        Initializes a pattern that checks against the
        given node, and optionally against the left and right
        nodes as well. The base Pattern implementation understands
        patters in the form of:
        * types:ASTType1,ASTType2
        * op:NodeType
        * ops:Op1,Op2
        * value:ValueStr
        * AND

        As an example, a pattern like:
        types:CompareOperator AND op:=
        types:CompareOperator AND ops:=,>,>=

        Will match a comparison operator which checks for equality.
        """
        self.node_p = node_p
        self.left_p = left_p
        self.right_p = right_p

    def matches(self, node):
        "Returns if the current node matches the pattern"
        if not self._check_pattern(self.node_p, node):
            return False
        if self.left_p and not self._check_pattern(self.left_p, node.left):
            return False
        if self.right_p and not self._check_pattern(self.right_p, node.right):
            return False
        return True

    @classmethod
    def _check_pattern(cls, pattern, node):
        # Support sub-classes of pattern
        if isinstance(pattern, Pattern):
            return pattern.matches(node)

        clauses = pattern.split(" AND ")
        for clause in clauses:
            # Check the node type
            if clause.startswith("types:"):
                types = clause[6:].split(",")
                if cls.node_type(node) not in types:
                    return False

            # Check the node op
            elif clause.startswith("op:"):
                op = clause[3:]
                if cls.node_op(node) != op:
                    return False

            # Check the node ops
            elif clause.startswith("ops:"):
                ops = clause[4:].split(",")
                if cls.node_op(node) not in ops:
                    return False

            # Check the node op
            elif clause.startswith("value:"):
                val = clause[6:]
                if cls.node_value(node) != val:
                    return False

            else:
                raise Exception("Invalid pattern clause %s" % clause)
        return True

    @classmethod
    def node_type(cls, node):
        return node.__class__.__name__

    @classmethod
    def node_op(cls, node):
        if hasattr(node, "type"):
            return node.type
        else:
            return None

    @classmethod
    def node_value(cls, node):
        if hasattr(node, "value"):
            return str(node.value)
        else:
            return None


def tile(ast, patterns, func):
    """
    Tiles over the given AST tree with a list of patterns,
    applying each. When a given pattern matches, the callback
    function is invoked with the pattern, and current node.
    The function can return either None or a new AST node
    which replaces the node that was passed in.

    Returns the new AST tree.
    """
    for p in patterns:
        if p.matches(ast):
            result = func(p, ast)
            if result is not None:
                ast=result

    # Tile the left
    if hasattr(ast, "left"):
        result = tile(ast.left, patterns, func)
        if result is not None:
            ast.left=result

    # Tile the right side
    if hasattr(ast, "right"):
        result = tile(ast.right, patterns, func)
        if result is not None:
            ast.right=result

    return ast

