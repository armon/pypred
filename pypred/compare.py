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
from tiler import ASTPattern, tile


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
    def replace_func(val, pattern, node):
        return ast.Constant(val)

    # Handle equality
    if name[1] == "equality":
        # Tile over the AST and replace the expresssion with
        # the assumed result
        pattern = ASTPattern(expr)
        node = tile(node, [pattern], partial(replace_func, assumed_result))

        # Tile over the AST and replace the inverse of the
        # expresssion with the opposite assumed result
        inverse = dup(expr)
        if inverse.type in ("=", "is"):
            inverse.type = "!="
        else:
            inverse.type = "="
        pattern = ASTPattern(inverse)

        print "Re-write inverse", inverse.description()
        return tile(node, [pattern], partial(replace_func, not assumed_result))

    # Handle comparison
    elif name[1] == "order":
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
        # Tile over the AST and replace the expresssion with
        # the assumed result
        pattern = ASTPattern(expr)
        return tile(node, [pattern], partial(replace_func, assumed_result))

    else:
        assert False, "Unknown compare!"

    return node

