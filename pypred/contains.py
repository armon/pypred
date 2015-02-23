"""
This module helps do rewrites when there is a comparison
function involed. Comparisons are special, because if we
are allows to assume the result of an expression, we can
make other inferences. For example, if we assume "a > b",
then we know that "b < a", "b <=a" are both true, and
we can safely rewrite that as a constant.
"""
from collections import defaultdict

from . import ast
from . import util
from .tiler import ASTPattern, SimplePattern, tile

def select_rewrite_expression(settings, name, exprs):
    """
    Given an expression name and a list of expressions,
    tries to select an expression with the highest selectivity
    for use in AST re-writing.
    """
    # Get all the sets
    sets = [e.left.value for e in exprs]

    # Count the occurances of each element
    counts = defaultdict(int)
    total = 0
    for s in sets:
        for item in s:
            counts[item] += 1
            total += 1

    # Compute the hamonic mean of avg frequency per set
    scores = []
    total = float(total)
    for idx, s in enumerate(sets):
        freqs = [counts[i]/total for i in s]
        hm = util.harmonic_mean(freqs)
        scores.append((hm, exprs[idx]))

    # Reverse sort, get the highest score
    sorted(scores, key=lambda p: p[0], reverse=True)

    # Check if we hit our minimum threshold
    if scores[0][0] < settings.min_density:
        return None

    # Return the highest score
    return scores[0][1]


def contains_rewrite(node, name, expr, assumed_result):
    """
    Takes an AST tree (node), and an expression with its
    name. Returns a new AST tree with the expr taking the
    assumed_result value, with potential optimizations.
    """
    # Get the set from the rewrite expression
    expr_set = expr.left.value

    # Replace function to handle AST re-writes
    def replace_func(pattern, node):
        # Determine the subset based on the assumed result
        if assumed_result is True:
            set_prime = node.left.value & expr_set

            # If this set is a super-set of the expression,
            # then we can re-write to true
            if set_prime == expr_set:
                return ast.Constant(True)

            # If there is no overlap, we are false
            elif len(set_prime) == 0:
                return ast.Constant(False)

            # Check if the set difference is smaller, and use negate
            set_prime_diff = expr_set - node.left.value
            if len(set_prime_diff) < len(set_prime):
                node.left.value = set_prime_diff
                return ast.NegateOperator(node)

        else:
            set_prime = node.left.value - expr_set

            # If we end up with the empty set
            # meaning subset, then its false
            if len(set_prime) == 0:
                return ast.Constant(False)

        # Alter the set we are checking
        node.left.value = set_prime
        return None

    # Tile to replace
    pattern = SimplePattern("types:ContainsOperator",
            "types:LiteralSet", ASTPattern(expr.right))
    return tile(node, [pattern], replace_func)

