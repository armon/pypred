"""
This module helps with the logic of merging
multiple AST trees together so that they can
be evaluated in a single pass. At the heart of the
algorithm is the merging of common expressions and
using branches.
"""
from functools import partial
from tiler import SimplePattern, tile

def merge(predicates):
    """
    Invoked with a set of predicates that should
    be merged into a single AST. The new AST uses
    the PushResults node to return the list of matching
    predicates.
    """
    return None

def count_expressions(ast):
    """
    Folds over the AST and counts the expressions that are
    can be refactored. Each named expression also maps to the
    AST nodes the name represents.

    Returns a tuple of (counts, names). The counts maps
    names to counts, and the names maps the name to AST nodes.
    """
    counts = {}
    nodes = {}

    # Get a partial application of the count function
    # that updates the proper dicts
    func = partial(count_func, counts, nodes)

    # Tile over the ast
    tile(ast, count_patterns(), func)

    # Return the counts
    return counts, nodes

def count_func(counts, nodes, pattern, node):
    "Invoked to count a new pattern being matched"
    # Convert to a hashable name
    name = node_name(node)

    # Increment the counter value for this expression and store the nodes
    counts[name] = counts.get(name, 0) + 1
    if name not in nodes:
        nodes[name] = node

def node_name(node):
    "Returns a hashable name that can be used for counting"
    cls_name = node.__class__.__name__
    if cls_name in ("Literal","Number","Constant","Regex"):
        return (cls_name, node.value)
    elif cls_name in ("Undefined", "Empty"):
        return cls_name
    elif cls_name == "NegateOperator":
        return (cls_name, node_name(node.left))
    elif cls_name == "CompareOperator":
        return (cls_name, node.type, node_name(node.left), node_name(node.right))
    elif cls_name in ("MatchOperator", "ContainsOperator"):
        return (cls_name, node_name(node.left), node_name(node.right))
    else:
        raise Exception("Unhandled class %s" % cls_name)

def count_patterns():
    "Returns the patterns that we can count"
    simple_types = "types:Literal,Number,Constant,Undefined,Empty"

    # Handle a negation of a simple type
    p1 = SimplePattern("types:NegateOperator", simple_types)

    # Handle comparison of a simple types
    p2 = SimplePattern("types:CompareOperator", simple_types, simple_types)

    # Handle regex matches
    p3 = SimplePattern("types:MatchOperator", simple_types, "types:Regex")

    # Handle simple contains
    p4 = SimplePattern("types:ContainsOperator", simple_types, simple_types)

    return [p1,p2,p3,p4]

