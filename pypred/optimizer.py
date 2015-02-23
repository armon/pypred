"""
This module helps to perform AST
re-writing to do simple optimizations.
"""
from functools import partial
from .tiler import tile, Pattern, SimplePattern
from . import ast
import collections

CACHE_PATTERNS = None


def optimize(node, max_pass=32, min_change=1):
    """
    Takes an AST and returns one that is equivilent
    but optimized.
    """
    changes = min_change
    passes = 0
    while passes < max_pass and changes >= min_change:
        changes, node = optimization_pass(node)
        passes += 1
    return node


def optimization_pass(node):
    """
    Does a single optimization pass.
    Returns (changes, ast). The number of changes
    should converge to 0 with enough passes.
    """
    # Get a partial application of the optimization function
    info = {'c': 0}
    func = partial(optimization_func, info)

    # Tile over the ast
    patterns = optimization_patterns()
    node = tile(node, patterns, func)

    # Return the counts
    return info['c'], node


def optimization_func(info, pattern, node):
    "Invoked to count an applied optimization and to replace"
    info['c'] += 1
    if isinstance(pattern.replacement, collections.Callable):
        return pattern.replacement(node)
    else:
        return pattern.replacement


def optimization_patterns():
    "Returns the patterns relevant for optimizations"
    global CACHE_PATTERNS
    if CACHE_PATTERNS:
        return CACHE_PATTERNS

    # Replace and AND with a False value with False
    p1 = SimplePattern("types:LogicalOperator AND op:and", "types:Constant AND value:False")
    p1.replacement = ast.Constant(False)

    p2 = SimplePattern("types:LogicalOperator AND op:and", None, "types:Constant AND value:False")
    p2.replacement = ast.Constant(False)

    # Replace OR with a True value with True
    p3 = SimplePattern("types:LogicalOperator AND op:or", "types:Constant AND value:True")
    p3.replacement = ast.Constant(True)

    p4 = SimplePattern("types:LogicalOperator AND op:or", None, "types:Constant AND value:True")
    p4.replacement = ast.Constant(True)

    # Replace a simple negation
    p5 = SimplePattern("types:NegateOperator", "types:Constant AND value:True")
    p5.replacement = ast.Constant(False)

    p6 = SimplePattern("types:NegateOperator", "types:Constant AND value:False")
    p6.replacement = ast.Constant(True)

    # Remove a no-op push result
    p7 = SimplePattern("types:PushResult", "types:Constant AND value:False")
    p7.replacement = ast.Constant(False)

    # Remove Both nodes when possible
    p8 = SimplePattern("types:Both", "types:Constant AND value:False", "types:Constant AND value:False")
    p8.replacement = ast.Constant(False)

    # Special pattern that replaces Both with one of the children
    p9 = ExtraBothPattern()

    # Remove logical operators when the short-circuit path is useless
    p10 = ShortCircuitLogicalPattern()

    # Remove dead branches
    p11 = DeadBranchPattern()

    # Remove empty sets
    p12 = SimplePattern("types:LiteralSet AND value:frozenset([])")
    p12.replacement = ast.Empty()

    # Replace "Empty contains *" with False
    p13 = SimplePattern("types:ContainsOperator", "types:Empty,Undefined")
    p13.replacement = ast.Constant(False)

    # Remove empty sets (python3)
    p14 = SimplePattern("types:LiteralSet AND value:frozenset()")
    p14.replacement = ast.Empty()

    CACHE_PATTERNS = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14]
    return CACHE_PATTERNS


class ExtraBothPattern(Pattern):
    """
    This pattern detects when there is a both, but one
    of the children is a no-op. This allows the Both
    to be replaced with one child.
    """
    def matches(self, node):
        if not isinstance(node, ast.Both):
            return False
        if self._replacement(node):
            return True
        return False

    def _replacement(self, node):
        # Check if the left node is useless
        if isinstance(node.left, ast.Constant) and node.left.value == False:
            return node.right

        # Check if the right node is useless
        if isinstance(node.right, ast.Constant) and node.right.value == False:
            return node.left
        return None

    def replacement(self, node):
        r = self._replacement(node)
        if r:
            return r
        raise Exception("No valid replacement!")


class ShortCircuitLogicalPattern(Pattern):
    """
    This pattern detects when there is a logical operation
    where the short-circuit path is a noop, and replaces it
    with the other path.

    For example true and expr can be replace with expr,
    or false or expr could be replaced with expr.
    """
    def matches(self, node):
        if not isinstance(node, ast.LogicalOperator):
            return False
        if self._replacement(node):
            return True
        return False

    def _replacement(self, node):
        if isinstance(node.left, ast.Constant):
            # true and expr -> expr
            if node.type == "and" and node.left.value == True:
                return node.right

            # false or expr -> expr
            if node.type == "or" and node.left.value == False:
                return node.right

        elif isinstance(node.right, ast.Constant):
            # expr and true -> expr
            if node.type == "and" and node.right.value == True:
                return node.left

            # expr or false -> expr
            if node.type == "or" and node.right.value == False:
                return node.left

        return None

    def replacement(self, node):
        r = self._replacement(node)
        if r:
            return r
        raise Exception("No valid replacement!")


class DeadBranchPattern(Pattern):
    """
    This pattern detects when there is a dead branch that
    is unreachable. It replaces it with the proper live branch.
    """
    def matches(self, node):
        if not isinstance(node, ast.Branch):
            return False

        # Check for a constant expression
        return isinstance(node.expr, ast.Constant)

    def replacement(self, node):
        branch = node.expr.value
        if branch:
            return node.left if node.left else ast.Constant(False)
        else:
            return node.right if node.right else ast.Constant(False)

