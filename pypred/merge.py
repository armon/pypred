"""
This module helps with the logic of merging
multiple AST trees together so that they can
be evaluated in a single pass. At the heart of the
algorithm is the merging of common expressions and
using branches.
"""
from collections import defaultdict

from . import ast
from . import cache
from . import compare
from . import contains
from . import compact
from . import util
from .ast import dup
from .optimizer import optimize
from .tiler import ASTPattern, SimplePattern, tile

CACHE_PATTERNS = None

class RefactorSettings():
    def __init__(self, max_depth, min_select, max_opt_pass, min_change, min_density):
        """
        Defines the settings for a refactor. Parameters:
        -`max_depth` - Maximum branch depth of the tree. This causes
         the tree to grow by O(2^N) at worst in terms of nodes.
         However, at best it does reduce evaluations by O(2^N).

        -`min_select` - The minimum count of an expression before
         it is not eligible for being pushed into a branch. This can
         cause certain paths of the tree to have fewer branches.

        -`max_opt_pass` - Maximum number of optimization passes.
          This restricts the runs of the optimizer. Generally not
          recommended, instead min_change should be used to stop.

        -`min_change` - Minimum changes in a pass of the optimizer
         before the optimizer terminates. Best to set this to 1 and
         allow the optimizer to run until there are no further changes.

        -`min_density` - Minimum average density of a LiteralSet before
         it is eligible to be used as a branching expression. Setting this
         too low can cause useless branches.
        """
        self.max_depth = max_depth
        self.min_select = min_select
        self.max_opt_pass = max_opt_pass
        self.min_change = min_change
        self.min_density = min_density

        self.static_rewrite = True
        self.canonicalize = True
        self.initial_optimize = True
        self.refactor = True
        self.compact = True
        self.cache_expr = True

    @classmethod
    def minimum(cls):
        """
        Returns settings that should run very fast,
        but does very minimal pruning.

        Worst case blow up of 4 times (2^2).
        """
        return RefactorSettings(2, 8, 32, 1, 0.1)

    @classmethod
    def shallow(cls):
        """
        Returns settings that should run relatively fast.
        Maximum branch depth of 4, selectivity of 32, and
        largely unrestricted optimization.

        Worst case blow up of 16 times (2^4).
        """
        return RefactorSettings(4, 16, 32, 1, 0.05)

    @classmethod
    def deep(cls):
        """
        Returns settings that should prune very well.
        Maximum branch depth of 8, selectivity of 16, and
        largely unrestricted optimization.

        Worst case blow up of 256 times (2^8).
        """
        return RefactorSettings(8, 32, 32, 1, 0.03)

    @classmethod
    def extreme(cls):
        """
        Returns settings that should prune with extreme
        branching. This will be very slow.

        Worst case blow up of 65536 times (2^16).
        """
        return RefactorSettings(16, 64, 32, 1, 0.01)


def merge(predicates):
    """
    Invoked with a set of predicates that should
    be merged into a single AST. The new AST uses
    the PushResults node to return the list of matching
    predicates, and Both nodes to combine.
    """
    # Merge the AST tree's together first using a tree
    all_asts = [ast.PushResult(p, dup(p.ast)) for p in predicates]
    while len(all_asts) > 1:
        merged = []
        end = len(all_asts)
        for x in range(0, end, 2):
            if x+1 == end:
                merged.append(all_asts[x])
            else:
                both = ast.Both(all_asts[x], all_asts[x+1])
                merged.append(both)
        all_asts = merged

    # The root object has everything
    return all_asts[0]


def refactor(pred_set, ast, settings=None):
    """
    Performs a refactor of an AST tree to
    get the maximum selectivity and minimze wasted
    evaluations. Settings are controlled using
    a RefactorSettings object. If none is provided
    the `shallow` settings are used.
    """
    # Determine our settings
    if settings is None:
        settings = RefactorSettings.shallow()

    # Perform static resolution of all literals
    if settings.static_rewrite:
        static_resolution(ast, pred_set)

    # Canonicalize the AST
    if settings.canonicalize:
        ast = compare.canonicalize(ast)

    # Do an initial optimization pass for easy wins
    if settings.initial_optimize:
        ast = optimize(ast, settings.max_opt_pass, settings.min_change)

    # Recursively rebuild the tree to optimize cost
    if settings.refactor:
        ast = recursive_refactor(ast, settings)

    # Perform static resolution of all literals again, since
    # literal sets may have changed
    if settings.static_rewrite:
        static_resolution(ast, pred_set)

    # Compact the tree
    if settings.compact:
        compact.compact(ast)

    # Cache any common expressions
    if settings.cache_expr:
        cache.cache_expressions(ast)

    return ast


def static_resolution(ast, pred):
    "Attempts to statically resolve all literals."
    def resolve_func(pattern, literal):
        literal.static_resolve(pred)

    pattern = SimplePattern("types:Literal,LiteralSet")
    tile(ast, [pattern], resolve_func)


def recursive_refactor(node, settings, depth=0):
    """
    Recursively refactors an AST tree. At each step,
    we determine the most expensive expression, and move
    it to the root as part of a branch. We then create a
    left and right AST in which the expression has been
    replaced with a constant.
    """
    # Check for max depth
    if depth == settings.max_depth:
        return node

    # Do the cost calculation
    count, names = count_expressions(node)

    # Iterate over expressions until we find a suitable expression
    expr = None
    for max, name in util.max_count(count):
        # Base case is that there is no further reductions
        if max < settings.min_select:
            return node

        # We now take the expression and do a simple
        # path expansion. We have a "true" (left) branch,
        # that assumes the expression is true. Then we have
        # a "false" (right) branch. Each branch has the
        # expression re-written into a constant value
        # and then we do an optimization pass.
        expr = select_rewrite_expression(settings, name, names[name])
        if expr is not None:
            break

    # If we don't find an expression, finish
    if expr is None:
        return node

    # Do a deep copy on the left side, since we
    # are re-writing the tree, re-use the right side
    left = dup(node)
    left = rewrite_ast(left, name, expr, True)
    left = optimize(left, settings.max_opt_pass, settings.min_change)
    left = recursive_refactor(left, settings, depth+1)

    right = rewrite_ast(node, name, expr, False)
    right = optimize(right, settings.max_opt_pass, settings.min_change)
    right = recursive_refactor(right, settings, depth+1)

    # Now we can push the most common expression into
    # a branch, and conditionally execute the sub-ast's
    return ast.Branch(expr, left, right)


def select_rewrite_expression(settings, name, exprs):
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

    # Check if this is a contains operator. The contains operator
    # uses static rewriting if we are operating on LiteralSets
    elif name[0] == "ContainsOperator" and name[1] == 'LiteralSet':
        return contains.select_rewrite_expression(settings, name, exprs)

    # For negate operators, use the sub-expression
    elif isinstance(exprs[0], ast.NegateOperator):
        return exprs[0].left

    # For logical operators, use the Literal sub-expression
    elif isinstance(exprs[0], ast.LogicalOperator):
        if isinstance(exprs[0].left, ast.Literal):
            return exprs[0].left
        else:
            return exprs[0].right

    # Use the first expression, as they are all the same
    return exprs[0]


def rewrite_ast(node, name, expr, assumed_result):
    """
    Based on the assumed value of an expression, re-writes
    the AST tree to constants where possible.
    """
    if name[0] == "CompareOperator":
        return compare.compare_rewrite(node, name, expr, assumed_result)

    elif name[0] == "ContainsOperator" and name[1] == 'LiteralSet':
        return contains.contains_rewrite(node, name, expr, assumed_result)

    else:
        # Tile over the AST and replace the expresssion
        const = ast.Constant(assumed_result)
        func = lambda p, n: const
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

    elif cls_name == "LiteralSet":
        return cls_name

    elif cls_name == "Number":
        if enable_static:
            return (cls_name, "static")
        else:
            return (cls_name, node.value)

    elif cls_name in ("Constant","Regex"):
        return (cls_name, node.value)

    elif cls_name in ("Undefined", "Empty"):
        return cls_name

    elif cls_name == "NegateOperator":
        # Return the name of the sub-expression, since if
        # we do a constant re-write of that, the optimizer
        # can replace the negate operator
        return node_name(node.left)

    elif cls_name == "CompareOperator":
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

    elif cls_name == "LogicalOperator":
        # Return the name of the literal sub-expression, since
        # the optimizer can use that to remove the logical operator
        l_name = node_name(node.left)
        if l_name[0] == "Literal":
            return l_name
        else:
            return node_name(node.right)

    elif cls_name in ("MatchOperator", "ContainsOperator"):
        return (cls_name, node_name(node.left), node_name(node.right))
    else:
        raise Exception("Unhandled class %s" % cls_name)


def count_patterns():
    "Returns the patterns that we can count"
    global CACHE_PATTERNS
    if CACHE_PATTERNS:
        return CACHE_PATTERNS

    simple_types = "types:Literal,LiteralSet,Number,Constant,Undefined,Empty"

    # Handle a negation of a simple type
    p1 = SimplePattern("types:NegateOperator", "types:Literal")

    # Handle comparison of a simple types
    p2 = SimplePattern("types:CompareOperator", simple_types, simple_types)

    # Handle regex matches
    p3 = SimplePattern("types:MatchOperator", simple_types)

    # Handle simple contains
    p4 = SimplePattern("types:ContainsOperator", simple_types, simple_types)

    # Handle simple logical expressions
    p5 = SimplePattern("types:LogicalOperator", "types:Literal", None)
    p6 = SimplePattern("types:LogicalOperator", None, "types:Literal")

    CACHE_PATTERNS = [p1,p2,p3,p4,p5,p6]
    return CACHE_PATTERNS

