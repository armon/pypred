"""
This module helps do rewrites when there is a comparison
function involed. Comparisons are special, because if we
are allows to assume the result of an expression, we can
make other inferences. For example, if we assume "a > b",
then we know that "b < a", "b <=a" are both true, and
we can safely rewrite that as a constant.
"""
import ast
import util
from tiler import ASTPattern, SimplePattern, tile

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
    elif name[1] == "order" and name[3][1] == "static":
        values = [e.right.value for e in exprs]
        filter_using = util.median(values)
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
            elif node.type in INEQUALITY:
                const = not known

        # If we can't do a rewrite, just skip this node
        return ast.Constant(const) if const is not None else None

    # Tile to replace
    pattern = SimplePattern("types:CompareOperator AND ops:=,!=,is", ASTPattern(expr.left))
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
    # Get the literal and static compare values
    static_value = expr.right.value
    numeric = isinstance(expr.right, ast.Number)

    # Based on the assumed result
    less_than = "<" in expr.type
    maybe_equals = "=" in expr.type
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

            if less_than and assert_less:
                # a <= b, a < c -> c > b
                if maybe_equals and not assert_equals:
                    if node_val > static_value:
                        const = True

                # a < b, a < c -> c >= b
                else:
                    if node_val >= static_value:
                        const = True

            elif not less_than and not assert_less:
                # a >=b, a > c -> c < b
                if maybe_equals and not assert_equals:
                    if node_val < static_value:
                        const = True

                # a > b, a > c -> c <= b
                else:
                    if node_val <= static_value:
                        const = True

            elif less_than and not assert_less:
                # a <= b, a > c -> iff c > b False
                if maybe_equals and not assert_equals:
                    if node_val > static_value:
                        const = False

                # a < b, a >= c -> iff c >= b False
                else:
                    if node_val >= static_value:
                        const = False

            elif not less_than and assert_less:
                # a >= b, a < c -> iff c < b True
                if maybe_equals and not assert_equals:
                    if node_val < static_value:
                        const = False

                # a > b, a <= c -> iff c <= b False
                else:
                    if node_val <= static_value:
                        const = False

        # No replacement in some situations
        if const is None:
            return None
        return ast.Constant(const)


    # Tile to replace
    pattern = SimplePattern("types:CompareOperator AND ops:<,<=,>,>=",
            ASTPattern(expr.left), "types:Number" if numeric else "types:Literal")
    return tile(node, [pattern], replace_func)

