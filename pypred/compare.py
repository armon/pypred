"""
This module helps do rewrites when there is a comparison
function involed. Comparisons are special, because if we
are allows to assume the result of an expression, we can
make other inferences. For example, if we assume "a > b",
then we know that "b < a", "b <=a" are both true, and
we can safely rewrite that as a constant.
"""
from functools import partial

import ast
import util
from ast import dup
from tiler import SimplePattern, ASTPattern, tile


def select_rewrite_expression(name, exprs):
    """
    Given an expression name and a list of expressions,
    tries to select an expression with the highest selectivity
    for use in AST re-writing.
    """
    # Are the static values on the left hand side?
    if name[2][1] == "static":
        side = "left"
        values = [e.left.value for e in exprs]
    # Right hande side
    elif name[3][1] == "static":
        side = "right"
        values = [e.right.value for e in exprs]
    else:
        assert False, "No static value found!"

    # For equality check (=, !=, is), select the most mode
    if name[1] == "equality":
        filter_using = util.mode(values)
        for e in exprs:
            if getattr(e, side).value == filter_using:
                return e

    # For ordering checks, select the median value
    elif name[1] == "order":
        filter_using = util.median(values)
        for e in exprs:
            if getattr(e, side).value == filter_using:
                return e

    assert False, "Failed to select expression!"


def compare_rewrite(node, name, expr, assumed_result):
    """
    Takes an AST tree (node), and an expression with its
    name. Returns a new AST tree with the expr taking the
    assumed_result value, with potential optimizations.
    """
    # Handle equality
    if name[1] == "equality":
        return equality_rewrite(node, name, expr, assumed_result)

    # Handle comparison
    elif name[1] == "order":
        return order_rewrite(node, name, expr, assumed_result)

    else:
        assert False, "Unknown compare!"


def equality_rewrite(node, name, expr, assumed_result):
    # Determine the literal and static value
    if name[2][1] == "static":
        l_side = "right"
        v_side = "left"
        literal = expr.right.value
        static_value = expr.left.value

    # Right hande side
    else:
        l_side = "left"
        v_side = "right"
        literal = expr.left.value
        static_value = expr.right.value

    # Replace function to handle AST re-writes
    def replace_func(pattern, node):
        # Ignore if no match on the literal
        if getattr(node, l_side).value != literal:
            return None

        # Do the static comparison
        val = getattr(node, v_side).value
        static_match = val == static_value

        # Do we 'know' the value
        if expr.type in ("=", "is"):
            known = True
        else:
            known = False

        if not assumed_result:
            known = not known

        # Check comparison to known result
        if known:
            if node.type in ("=", "is"):
                const = static_match
            else:
                const = not static_match

        # Is the comparison against the static match
        elif static_match:
            if node.type in ("=", "is"):
                const = False
            else:
                const = True

        # If it is being compared against another
        # value, we aren't sure what to do
        else:
            return None

        return ast.Constant(const)

    # Simple pattern for CompareOperators
    pattern = SimplePattern("types:CompareOperator",
            "types:Literal" if l_side == "left" else None,
            "types:Literal" if l_side == "right" else None)

    # Tile to replace
    return tile(node, [pattern], replace_func)


def order_rewrite(node, name, expr, assumed_result):
    """
    IFF
    a > b is True:
      * a < b is False
      * a <= b is False

      * b > a is False
      * b >= a is False

      * b < a is True
      * b <= a is True

    a >= b is True:
      * a < b is False
      * b > a is False
      * b <= a is True
    """
    def replace_func(val, pattern, node):
        return ast.Constant(val)

    # Tile over the AST and replace the expresssion with
    # the assumed result
    pattern = ASTPattern(expr)
    return tile(node, [pattern], partial(replace_func, assumed_result))

