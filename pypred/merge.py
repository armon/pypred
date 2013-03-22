"""
This module helps with the logic of merging
multiple AST trees together so that they can
be evaluated in a single pass. At the heart of the
algorithm is the merging of common expressions and
using branches.
"""
from collections import defaultdict

import ast
import compare
import util
from ast import dup
from optimizer import optimize
from tiler import ASTPattern, SimplePattern, tile

CACHE_PATTERNS = None


def merge(predicates):
    """
    Invoked with a set of predicates that should
    be merged into a single AST. The new AST uses
    the PushResults node to return the list of matching
    predicates, and Both nodes to combine.
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

    # The root object has everything
    return  all_asts[0]


def refactor(pred_set, ast):
    """
    Performs a refactor of an AST tree to
    get the maximum selectivity and minimze wasted
    evaluations
    """
    # Perform static resolution of all literals
    static_resolution(ast, pred_set)

    # Recursively rebuild the tree to optimize cost
    return recursive_refactor(ast)


def static_resolution(ast, pred):
    "Attempts to statically resolve all literals."
    def resolve_func(pattern, literal):
        literal.static_resolve(pred)

    pattern = SimplePattern("types:Literal")
    tile(ast, [pattern], resolve_func)


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
    max, name = util.max_count(count)

    # Base case is that there is no further reductions
    if max <= min_count:
        return node
    print "Refactoring", depth, name, max

    # We now take the expression and do a simple
    # path expansion. We have a "true" (left) branch,
    # that assumes the expression is true. Then we have
    # a "false" (right) branch. Each branch has the
    # expression re-written into a constant value
    # and then we do an optimization pass.
    expr = select_rewrite_expression(name, names[name])
    print "Re-write expr", expr.description()

    # Do a deep copy on the left side, since we
    # are re-writing the tree, re-use the right side
    left = dup(node)
    left = rewrite_ast(left, name, expr, True)
    left = optimize(left)
    left = recursive_refactor(left, depth+1)

    right = rewrite_ast(node, name, expr, False)
    right = optimize(right)
    right = recursive_refactor(right, depth+1)

    # Now we can push the most common expression into
    # a branch, and conditionally execute the sub-ast's
    return ast.Branch(expr, left, right)


def select_rewrite_expression(name, exprs):
    """
    Selects an expression to use for re-writing
    based on a list of possible expressions.
    """
    # Check if this is a compare operator. The compare
    # operator is special since it uses a 'static' re-write
    # to group similar checks together. For example the checks
    # gender is 'Male' / gender is 'Female' get merged into
    # a compare against static.
    if name[0] == "CompareOperator":
        return compare.select_rewrite_expression(name, exprs)

    # Use the first expression, as they are all the same
    return exprs[0]


def rewrite_ast(node, name, expr, assumed_result):
    """
    Based on the assumed value of an expression, re-writes
    the AST tree to constants where possible.
    """
    if name[0] == "CompareOperator":
        return compare.compare_rewrite(node, name, expr, assumed_result)
    else:
        # Tile over the AST and replace the expresssion
        func = lambda pattern, node: ast.Constant(assumed_result)
        pattern = ASTPattern(expr)
        return tile(node, [pattern], func)


def count_expressions(node):
    """
    Folds over the AST and counts the expressions that are
    can be refactored. Each named expression also maps to the
    AST nodes the name represents.

    Returns a tuple of (counts, names). The counts maps
    names to counts, and the names maps the name to AST nodes.
    """
    counts = defaultdict(int)
    nodes = defaultdict(list)

    def count_func(pattern, node):
        "Invoked to count a new pattern being matched"
        # Convert to a hashable name
        enable_static = isinstance(node, ast.CompareOperator)
        name = node_name(node, enable_static)

        # Increment the counter value for this expression and store the nodes
        counts[name] += 1
        nodes[name].append(node)

    # Return the counts
    tile(node, count_patterns(), count_func)
    return counts, nodes


def node_name(node, enable_static=False):
    "Returns a hashable name that can be used for counting"
    cls_name = node.__class__.__name__
    if cls_name == "Literal":
        if enable_static and node.static:
            return (cls_name, "static")
        else:
            return (cls_name, node.value)
    elif cls_name in ("Number","Constant","Regex"):
        if enable_static:
            return (cls_name, "static")
        else:
            return (cls_name, node.value)
    elif cls_name in ("Undefined", "Empty"):
        return cls_name
    elif cls_name == "NegateOperator":
        return (cls_name, node_name(node.left, enable_static))
    elif cls_name in ("CompareOperator", "LogicalOperator"):
        if enable_static:
            n_type = node.type
            if n_type in ("=", "!=", "is"):
                type = "equality"
            elif n_type in (">", ">=", "<", "<="):
                type = "order"
            else:
                type = n_type
        else:
            type = node.type
        return (cls_name, type, node_name(node.left, enable_static), node_name(node.right, enable_static))
    elif cls_name in ("MatchOperator", "ContainsOperator"):
        return (cls_name, node_name(node.left, enable_static), node_name(node.right, enable_static))
    else:
        raise Exception("Unhandled class %s" % cls_name)


def count_patterns():
    "Returns the patterns that we can count"
    global CACHE_PATTERNS
    if CACHE_PATTERNS:
        return CACHE_PATTERNS

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

    CACHE_PATTERNS = [p1,p2,p3,p4,p5,p6,p7]
    return CACHE_PATTERNS

