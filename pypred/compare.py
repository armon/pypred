"""
This module helps do rewrites when there is a comparison
function involed. Comparisons are special, because if we
are allows to assume the result of an expression, we can
make other inferences. For example, if we assume "a > b",
then we know that "b < a", "b <=a" are both true, and
we can safely rewrite that as a constant.
"""
from . import ast
from . import util
from .tiler import ASTPattern, SimplePattern, tile

EQUALITY = ("=", "is")
INEQUALITY = ("!=",)


def canonicalize(node):
    """
    Rewrites the AST so that all comparisons are in a
    canonical order. This allows the expressions:
        gender is 'Male' / 'Male' is gender

    to be transformed into the same form. This makes
    refactoring expressions order independent.
    """
    def replace_func(pattern, n):
        l_literal = isinstance(n.left, ast.Literal)
        r_literal = isinstance(n.right, ast.Literal)

        # Always put the literal on the left
        if not l_literal and r_literal:
            n.reverse()

        elif l_literal and r_literal:
            # Put static values on the right
            if n.left.static and not n.right.static:
                n.reverse()

            # Put the literals in order (both non-static)
            elif not n.left.static and not n.right.static and n.left.value > n.right.value:
                n.reverse()

            # Put the literals in order (both static)
            elif n.left.static and n.right.static and n.left.value > n.right.value:
                n.reverse()

    p = SimplePattern("types:CompareOperator")
    return tile(node, [p], replace_func)


def select_rewrite_expression(name, exprs):
    """
    Given an expression name and a list of expressions,
    tries to select an expression with the highest selectivity
    for use in AST re-writing.
    """
    # For equality check (=, !=, is), select the mode
    if name[1] == "equality":
        values = [e.right.value for e in exprs]
        filter_using = util.mode(values)
        for e in exprs:
            if e.right.value == filter_using:
                return e

    # For ordering checks, select the median value for static
    elif name[1] == "order":
        is_static = name[3][1] == "static"
        values = [e.right.value for e in exprs]

        # For static (numeric) compares, we use median
        # value to eliminate as many as possible.
        # For non-numeric, we use mode
        if is_static:
            filter_using = util.median(values)
        else:
            filter_using = util.mode(values)

        for e in exprs:
            if e.right.value == filter_using:
                return e

    # For ordering checks without static values, use any
    else:
        return exprs[0]


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
    # Get the literal and static compare values
    static_value = expr.right.value
    is_static = expr.right.static

    # Do we 'know' the value to be something
    # specific, or can we just eliminate a possible value.
    if expr.type in EQUALITY:
        known = assumed_result
    else:
        known = not assumed_result

    # Replace function to handle AST re-writes
    def replace_func(pattern, node):
        # Do the static comparison
        static_match = node.right.value == static_value
        is_static_node = node.right.static

        # If we are refactoring equality on a static
        # variable, then we can statically perform the comparisons
        # and do more aggressive rewrites of the AST.
        const = None
        if known and is_static and is_static_node:
            if node.type in EQUALITY:
                const = static_match
            else:
                const = not static_match

        # If we are refactoring equality on a non-static
        # variable, then we have a limit set of rewrites.
        # for example, if a = b, then a = c could also be true,
        # since b = c is possible.
        elif static_match:
            if node.type in EQUALITY:
                const = known
            else:
                const = not known

        # If we can't do a rewrite, just skip this node
        return ast.Constant(const) if const is not None else None

    # Tile to replace
    pattern = SimplePattern("types:CompareOperator AND ops:=,!=,is", ASTPattern(expr.left))
    return tile(node, [pattern], replace_func)


def order_rewrite(node, name, expr, assumed_result):
    # Get the literal and static compare values
    static_value = expr.right.value
    numeric = isinstance(expr.right, ast.Number)

    # Based on the assumed result get the upper/lower bounds
    less_than = "<" in expr.type
    maybe_equals = "=" in expr.type
    if less_than:
        if assumed_result:
            min_bound = float("-inf")
            min_incl = False
            max_bound = static_value
            max_incl = maybe_equals
        else:
            min_bound = static_value
            min_incl = not maybe_equals
            max_bound = float("inf")
            max_incl = False
    else:
        if assumed_result:
            min_bound = static_value
            min_incl = maybe_equals
            max_bound = float("inf")
            max_incl = False
        else:
            min_bound = float("-inf")
            min_incl = False
            max_bound = static_value
            max_incl = not maybe_equals

    if not assumed_result:
        less_than = not less_than
        maybe_equals = not maybe_equals

    # Replace function to handle AST re-writes
    def replace_func(pattern, node):
        node_val = node.right.value
        if not numeric and node_val != static_value:
            return None

        # Check what this node is asserting
        assert_less = "<" in node.type
        assert_equals = "=" in node.type

        # For literals, check that assertions match
        if not numeric:
            const = (less_than == assert_less)
            if maybe_equals:
                const = const and assert_equals

        # For numerics we can do static analysis
        else:
            # Some cases cannot be re-written
            const = None
            if assert_less:
                # a < c, c > b iff a < b
                if node_val > max_bound:
                    const = True

                # a <= c, c = b iff a <= b
                # a < c, c = b iff a <= b UNKNOWN!
                elif node_val == max_bound and max_incl and assert_equals:
                    const = True

                # a < c, c == b, a < b
                # a <= c, c == b, a < b
                elif node_val == max_bound and not max_incl:
                    const = True

                # a < 5, a > 6
                elif node_val < min_bound:
                    const = False

                # a < 5, a > 5
                # a < 5, a >= 5
                elif node_val == min_bound and not assert_equals:
                    const = False

                # a <= 5, a > 5
                # a <= 5, a >= 5 UNKNOWN!
                elif node_val == min_bound and assert_equals and \
                    not min_incl:
                    const = False

            else:
                # a > c, c < b iff a > b
                if node_val < min_bound:
                    const = True

                # a >= c, c = b iff a > b
                # a > c, c = b iff a > b
                elif node_val == min_bound and not min_incl:
                    const = True

                # a >= c, c = b iff a >= b
                # a > c, c = b iff a >= b UNKNOWN!
                elif node_val == min_bound and min_incl and assert_equals:
                    const = True

                # a > c, c > b iff a < b
                elif node_val > max_bound:
                    const = False

                # a > 5, a < 5
                # a > 5, a <= 5
                elif node_val == max_bound and not assert_equals:
                    const = False

                # a >= 5, a < 5
                # a >= 5, a <= 5 UNKNOWN!
                elif node_val == max_bound and assert_equals and \
                    not max_incl:
                    const = False

        # No replacement in some situations
        if const is None:
            return None
        return ast.Constant(const)


    # Tile to replace
    pattern = SimplePattern("types:CompareOperator AND ops:<,<=,>,>=",
            ASTPattern(expr.left), "types:Number" if numeric else "types:Literal")
    return tile(node, [pattern], replace_func)

