"""
This module helps with the logic of merging
multiple AST trees together so that they can
be evaluated in a single pass. At the heart of the
algorithm is the merging of common expressions and
using branches.
"""
from copy import deepcopy
from functools import partial
from tiler import ASTPattern, SimplePattern, tile
from optimizer import optimize
import ast

def merge(predicates):
    """
    Invoked with a set of predicates that should
    be merged into a single AST. The new AST uses
    the PushResults node to return the list of matching
    predicates.
    """
    # Nothing to do if only given a single predicate
    if len(predicates) == 1:
        return predicates[0]

    # Merge the AST tree's together first using a tree
    all_asts = [ast.PushResult(p, dup(p.ast)) for p in predicates]
    while len(all_asts) > 1:
        merged = []
        end = len(all_asts)
        for x in xrange(0, end, 2):
            if x+1 == end:
                merged.append(all_asts[x])
            else:
                both = ast.Both(all_asts[x], all_asts[x+1])
                merged.append(both)
        all_asts = merged

    # Recursively rebuild the tree to optimize cost
    return recursive_refactor(all_asts[0])

def dup(ast):
    "Duplicates an AST tree"
    return deepcopy(ast)

def recursive_refactor(node, depth=0, max_depth=8, min_count=2):
    """
    Recursively refactors an AST tree. At each step,
    we determine the most expensive expression, and move
    it to the root as part of a branch. We then create a
    left and right AST in which the expression has been
    replaced with a constant.
    """
    # Check for max depth
    if depth == max_depth:
        return node

    # Do the cost calculation
    count, names = count_expressions(node)
    max, name = max_count(count)

    # Base case is that there is no further reductions
    if max <= min_count:
        return node
    expr = names[name]
    print "Refactoring", depth, name, max

    # Do constant re-writing on the sub-trees
    # Do a deep copy on the left side, since we
    # are re-writing the tree, keep the right side
    left = deepcopy(node)
    left = rewrite_ast(left, expr, ast.Constant(True))
    left = optimize(left)
    left = recursive_refactor(left, depth+1)

    right = rewrite_ast(node, expr, ast.Constant(False))
    right = optimize(right)
    right = recursive_refactor(right, depth+1)

    # Now we can push the most common expression into
    # a branch, and conditionally execute the sub-ast's
    return ast.Branch(expr, left, right)


def rewrite_ast(ast, expr, replacement):
    """
    Tries to rewrite part of the AST and does
    node replacement. This is to do the constant
    re-writing.
    """
    def replace_func(pattern, node):
        return replacement

    # Tile over the AST and replace the expresssion
    pattern = ASTPattern(expr)
    return tile(ast, [pattern], replace_func)


def max_count(count):
    "Returns the maximum count with its name"
    max_count = 0
    max_name = None
    for n, c in count.iteritems():
        if c > max_count:
            max_count = c
            max_name = n
    return (max_count, max_name)

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
    elif cls_name in ("CompareOperator", "LogicalOperator"):
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

    # Handle simple logical expressions
    p5 = SimplePattern("types:LogicalOperator", simple_types, None)
    p6 = SimplePattern("types:LogicalOperator", None, simple_types)
    p7 = SimplePattern("types:LogicalOperator", simple_types, simple_types)

    return [p1,p2,p3,p4,p5,p6,p7]

