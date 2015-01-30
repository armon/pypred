"""
This module helps to optimize an AST tree by replacing
duplicate expressions with a cached expression.
"""
from collections import defaultdict

from . import ast
from .compact import node_name
from .tiler import tile, Pattern


def cache_expressions(node):
    "Modifies the AST tree in place to reduce the duplicated computations."
    # Count the occurance of each expression
    counts = defaultdict(int)
    def count_func(pattern, node):
        name = node_name(node)
        if isinstance(name, tuple) and "Operator" in name[0]:
            counts[name] += 1
    tile(node, [Pattern()], count_func)

    # Replace all the expressions with count > 1 with
    # a cached version
    state = {"last_id": 0}
    replacements = {}
    def repl_func(pattern, node):
        # Check for a cached node
        name = node_name(node)
        if name and name in counts and counts[name] > 1:
            if name in replacements:
                return replacements[name]
            else:
                cache_node = ast.CachedNode(node, state["last_id"])
                replacements[name] = cache_node
                state["last_id"] += 1
                return cache_node

    tile(node, [Pattern()], repl_func)
    return node

