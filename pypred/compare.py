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
from tiler import SimplePattern, tile



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

        # Put the literals in order
        elif l_literal and r_literal and n.left.value > n.right.value:
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
    literal = expr.left.value
    static_value = expr.right.value

    # Do we 'know' the value
    if expr.type in ("=", "is"):
        known = True
    else:
        known = False

    if not assumed_result:
        known = not known

    # Replace function to handle AST re-writes
    def replace_func(pattern, node):
        # Ignore if not an equality check
        if node.type not in ("=", "!=", "is"):
            return None

        # Ignore if no match on the literal
        if node.left.value != literal:
            return None

        # Do the static comparison
        val = node.right.value
        static_match = val == static_value

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

    # Tile to replace
    pattern = SimplePattern("types:CompareOperator", "types:Literal")
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
    literal = expr.left.value
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
        # Ignore if not an ordering check
        if node.type not in ("<", "<=", ">", ">="):
            return None

        # Ignore if no match on the literal
        if node.left.value != literal:
            return None

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
    pattern = SimplePattern("types:CompareOperator",
            "types:Literal", "types:Number" if numeric else "types:Literal")
    return tile(node, [pattern], replace_func)

