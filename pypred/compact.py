"""
This module helps to 'compact' an AST tree by replacing
duplicate nodes with a reference to the same node.
"""
from .tiler import tile, Pattern


def compact(node):
    "Modifies the AST tree in place to reduce the duplicated nodes."
    cache = {}
    def repl_func(pattern, node):
        # Check for a cached node
        name = node_name(node)
        if name and name in cache:
            return cache[name]
        elif name:
            cache[name] = node

    tile(node, [Pattern()], repl_func)
    return node


def node_name(node):
    "Returns a hashable name that can be used for counting"
    cls_name = node.__class__.__name__
    if cls_name in ("Literal", "Number", "Constant", "Regex", "LiteralSet"):
        return (cls_name, node.value)

    elif cls_name in ("Undefined", "Empty"):
        return cls_name

    elif cls_name == "NegateOperator":
        return (cls_name, node_name(node.left))

    elif cls_name in ("CompareOperator", "LogicalOperator"):
        return (cls_name, node.type, node_name(node.left), node_name(node.right))

    elif cls_name in ("MatchOperator", "ContainsOperator"):
        return (cls_name, node_name(node.left), node_name(node.right))

    else:
        return None

