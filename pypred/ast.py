"""
This module provides the AST nodes that are used to
represent and later, evaluate a predicate.
"""
import re
from copy import deepcopy
from functools import wraps


class EvalContext(object):
    """
    Provides a context for the evaluation.
    Allows for transient state that is needed during
    an evaluation.
    """
    def __init__(self, predicate, doc, analyze=False):
        self.pred = predicate
        self.doc = doc
        self.literals = {}
        self.reach = 0
        self.failed = []
        self.cached_res = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.analyze = analyze
        self._analyze = analyze

    def __enter__(self):
        self.analyze = False

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.analyze = self._analyze

    def resolve_identifier(self, ident):
        return self.pred.resolve_identifier(self.doc, ident)


def dup(ast):
    "Duplicates an AST tree"
    return deepcopy(ast)


def failure_info(func):
    "Helper to provide error information on failure"
    @wraps(func)
    def wrapper(self, ctx):
        r = func(self, ctx)
        if not r and ctx.analyze:
            self.failure_info(ctx)
        return r
    return wrapper


class Node(object):
    "Root object in the AST tree"
    # Unknown default position
    position = "line: ?, col: ?"

    def set_position(self, line, col):
        self.position = "line: %d, col %d" % (line, col)

    def name(self):
        "Provides human name with location"
        cls = self.__class__.__name__
        return "%s at %s" % (cls, self.position)

    def description(self, buf=None, depth=0, max_depth=0):
        """
        Provides a human readable tree description
        """
        if not buf:
            buf = ""
        pad = depth * "\t"
        if max_depth and depth == max_depth:
            buf += pad + "...\n"
            return buf

        buf += pad + self.name() + "\n"
        if hasattr(self, "left"):
            buf = self.left.description(buf, depth+1, max_depth)
        if hasattr(self, "right"):
            buf = self.right.description(buf, depth+1, max_depth)
        return buf

    def __repr__(self):
        """
        Provides a representation that is useful to check the AST
        but is not necesarily very usable as a user error message.
        """
        name = self.__class__.__name__
        r = name
        if hasattr(self, "type"):
            r += " t:" + str(self.type)
        if hasattr(self, "value"):
            r += " v:" + str(self.value)
        if hasattr(self, "left"):
            r += " l:" + self.left.__class__.__name__
        if hasattr(self, "right"):
            r += " r:" + self.right.__class__.__name__
        return r

    def pre(self, func):
        """
        Performs a pre-order traversal of the
        tree, and invokes a callback for each node.
        """
        func(self)
        if hasattr(self, "left"):
            self.left.pre(func)
        if hasattr(self, "right"):
            self.right.pre(func)

    def validate(self, info=None):
        """
        Performs semantic validation of the Node.
        Attaches information to an info object,
        which is returned
        """
        if info is None:
            info = {"errors": [], "regex": {}}

        # Post order validation
        v = True
        if hasattr(self, "left"):
            sub_v, _ =  self.left.validate(info)
            v &= sub_v
        if hasattr(self, "right"):
            sub_v, _ = self.right.validate(info)
            v &= sub_v

        v &= self._validate(info)
        return (v, info)

    def _validate(self, info):
        "Validates the node"
        return True

    def evaluate(self, pred, document):
        """
        Evaluates the AST tree against the document for the
        given predicate. Returns either True or False
        """
        ctx = EvalContext(pred, document)
        return bool(self.eval(ctx))

    def analyze(self, pred, document):
        """
        Evaluates the AST tree against the document for the
        given predicate and provides the EvalContext with detailed
        information about the evaluation and failure reasons
        """
        ctx = EvalContext(pred, document, analyze=True)
        res = bool(self.eval(ctx))
        return res, ctx

    def eval(self, ctx):
        "Node-specific implementation"
        return True


class LogicalOperator(Node):
    "Used for the logical operators"
    def __init__(self, op, left, right):
        self.type = op
        self.left = left
        self.right = right

    def name(self):
        return "%s operator at %s" % (self.type.upper(), self.position)

    def _validate(self, info):
        "Validates the node"
        if self.type not in ("and", "or"):
            errs = info["errors"]
            errs.append("Unknown logical operator %s" % self.type)
            return False
        return True

    @failure_info
    def eval(self, ctx):
        "Implement short-circuit logic"
        if self.type == "and":
            if not self.left.eval(ctx):
                return False
            if not self.right.eval(ctx):
                return False
            return True
        else:
            if self.left.eval(ctx):
                return True
            if self.right.eval(ctx):
                return True
            return False

    def failure_info(self, ctx):
        with ctx:
            l = self.left.eval(ctx)
        if self.type == "and" and not l:
            err = "Left hand side of " + self.name() + " failed"
            ctx.failed.append(err)
            return

        if self.type == "or":
            err = "Both sides of " + self.name() + " failed"
        else:
            err = "Right hand side of " + self.name() + " failed"
        ctx.failed.append(err)


class NegateOperator(Node):
    "Used to negate a result"
    def __init__(self, expr):
        self.left = expr

    def name(self):
        return "not operator at %s" % (self.position)

    @failure_info
    def eval(self, ctx):
        return not self.left.eval(ctx)

    def failure_info(self, ctx):
        err = self.name() + " failed because sub-expression %s is true" % self.left.name()
        ctx.failed.append(err)


class CompareOperator(Node):
    "Used for all the mathematical comparisons"
    OP_REVERSE = {
            ">=": "<=", # a >= b -> b =< a
            ">": "<",   # a > b  -> b < a
            "<": ">",   # a < b  -> b > a
            "<=": ">=", # a <= b -> b >= a
            "=": "=",   # a = b  -> b = a
            "!=": "!=", # a != b -> b != a
            "is": "is"  # a is b -> b is a
    }

    def __init__(self, comparison, left, right):
        self.type = comparison
        self.left = left
        self.right = right

    def name(self):
        return "%s comparison at %s" % (self.type.upper(), self.position)

    def _validate(self, info):
        if self.type not in (">=", ">", "<", "<=", "=", "!=", "is"):
            errs = info["errors"]
            errs.append("Unknown compare operator %s" % self.type)
            return False
        return True

    def reverse(self):
        "Reverses the term order without changing eval"
        # Reverse left / right
        t = self.right
        self.right = self.left
        self.left = t

        # Reverse the op type
        self.type = self.OP_REVERSE[self.type]

    @failure_info
    def eval(self, ctx):
        left = self.left.eval(ctx)
        right = self.right.eval(ctx)

        # Check if this is an equality check
        if self.type in ("=", "is"):
            return left == right
        elif self.type == "!=":
            return left != right

        # Compare operations against undefined or empty always fail
        if isinstance(left, (Undefined, Empty)):
            return False
        if isinstance(right, (Undefined, Empty)):
            return False

        if self.type == ">=":
            return left >= right
        elif self.type == ">":
            return left > right
        elif self.type == "<=":
            return left <= right
        elif self.type == "<":
            return left < right

    def failure_info(self, ctx):
        with ctx:
            l = self.left.eval(ctx)
            r = self.right.eval(ctx)

        # Check if it was a failure due to undefined or empty
        if self.type not in ('=', '!=', 'is') and \
                isinstance(l, (Undefined, Empty)) or \
                isinstance(r, (Undefined, Empty)):
            err = self.name() + " failed with Undefined or Empty operand"
            ctx.failed.append(err)
            return

        # Comparison failure
        err = self.name() + " failed, left: %s, right: %s" % \
                (repr(l), repr(r))
        ctx.failed.append(err)


class ContainsOperator(Node):
    "Used for the 'contains' operator"
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def _validate(self, info):
        if not isinstance(self.right, (Number, Literal, Constant)):
            errs = info["errors"]
            errs.append("Contains operator must take a literal or constant! Got: %s for %s" % (repr(self.right), self.name()))
            return False
        return True

    @failure_info
    def eval(self, ctx):
        left = self.left.eval(ctx)
        if hasattr(left, "__contains__"):
            right = self.right.eval(ctx)
            return right in left
        return False

    def failure_info(self, ctx):
        with ctx:
            left = self.left.eval(ctx)
        if not hasattr(left, "__contains__"):
            err = "Left side: %s does not support contains for %s" \
                % (repr(left), self.name())
        else:
            with ctx:
                right = self.right.eval(ctx)
            err = "Right side: %s not in left side: %s for %s" \
                    % (repr(right), repr(left), self.name())

        ctx.failed.append(err)


class MatchOperator(Node):
    "Used for the 'matches' operator"
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def _validate(self, info):
        if not isinstance(self.right, Regex):
            errs = info["errors"]
            errs.append("%s must take a regex! Got: %s" % (self.name(), repr(self.right)))
            return False
        return True

    @failure_info
    def eval(self, ctx):
        left = self.left.eval(ctx)
        if not isinstance(left, str):
            return False

        right = self.right.eval(ctx)
        match = right.search(left)
        return match is not None

    def failure_info(self, ctx):
        with ctx:
            left = self.left.eval(ctx)
        re_str = self.right.value
        if not isinstance(left, str):
            err = "Regex %s argument %s not a string" % \
                    (repr(re_str), repr(left))
        else:
            err = "Regex %s does not match %s for %s" % \
                    (repr(re_str), repr(left), self.name())
        ctx.failed.append(err)


class Regex(Node):
    "Regular expression literal"
    def __init__(self, value):
        # Unpack a Node object if we are given one
        if isinstance(value, Node):
            self.value = value.value.strip("'\"")
            self.position = value.position
        else:
            self.value = value
        self.re = None

    def __deepcopy__(self, memo=None):
        return self

    def name(self):
        return "Regex %s at %s" % (repr(self.value), self.position)

    def _validate(self, info):
        if not isinstance(self.value, str):
            errs = info["errors"]
            errs.append("Regex at %s must be a string! Got: %s" % \
                    (self.position, repr(self.value)))
            return False

        # Try to compile
        try:
            self.re = re.compile(self.value)
        except (Exception) as e:
            errs = info["errors"]
            errs.append("Compilation failed for %s" % self.name())
            regexes = info["regex"]
            regexes[self.value] = str(e)
            return False

        return True

    def eval(self, ctx):
        if not self.re:
            self.re = re.compile(self.value)
        return self.re


class Literal(Node):
    "String literal"
    static = False
    static_val = None

    def __init__(self, value):
        self.value = value

    def __deepcopy__(self, memo=None):
        return self

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if isinstance(other, Literal):
            return self.value == other.value
        else:
            return False

    def name(self):
        return "Literal %s at %s" % (self.value, self.position)

    def static_resolve(self, pred):
        "Uses the predicate to perform a static resolution"
        s = pred.static_resolve(self.value)
        if isinstance(s, Undefined):
            return

        self.static = True
        self.static_val = s

    def eval(self, ctx):
        # Use the EvalContext to avoid any non-deterministic
        # resolution that can strange errors.
        if self.value in ctx.literals:
            return ctx.literals[self.value]

        # Use the predicate class to resolve the identifier
        if self.static:
            v = self.static_val
        else:
            v = ctx.resolve_identifier(self.value)

        # Cache the result
        ctx.literals[self.value] = v
        return v


class Number(Node):
    "Numeric literal"
    def __init__(self, value):
        try:
            self.value = float(value)
        except:
            self.value = value

    def __deepcopy__(self, memo=None):
        return self

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if isinstance(other, Number):
            return self.value == other.value
        else:
            return False

    def name(self):
        return "Number %f at %s" % (self.value, self.position)

    def _validate(self, info):
        if not isinstance(self.value, float):
            errs = info["errors"]
            errs.append("Failed to convert number at %s to float! Got: %s" % \
                    (self.position, self.value))
            return False
        return True

    def eval(self, ctx):
        return self.value


class Constant(Node):
    "Used for true, false, null"
    def __init__(self, value):
        self.value = value

    def __deepcopy__(self, memo=None):
        return self

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if isinstance(other, Constant):
            return self.value == other.value
        else:
            return False

    def name(self):
        return "Constant %s at %s" % (self.value, self.position)

    def _validate(self, info):
        if self.value not in (True, False, None):
            errs = info["errors"]
            errs.append("Invalid Constant at %s! Got: %s" % \
                    (self.position, self.value))
            return False
        return True

    def eval(self, ctx):
        return self.value


class Undefined(Node):
    "Represents a non-defined object"
    def __init__(self):
        return

    def __deepcopy__(self, memo=None):
        return self

    def __bool__(self):
        "Acts like False"
        return False

    # Python 2 legacy
    def __nonzero__(self):
        "Acts like False."
        return False

    def __contains__(self, o):
        return False

    def __hash__(self):
        return hash(None)

    def __eq__(self, other):
        "Only equal to undefined"
        return isinstance(other, (Undefined, Empty))

    def __ne__(self, other):
        """
        Comparing undefined to another undefined works,
        but fails against any other type
        """
        if isinstance(other, Undefined):
            return False
        return True

    def eval(self, ctx):
        return self


class Empty(Node):
    "Represents the null set"
    def __init__(self):
        return

    def __deepcopy__(self, memo=None):
        return self

    def __bool__(self):
        "Acts like False"
        return False

    # Python 2 legacy
    def __nonzero__(self):
        "Acts like False."
        return False

    def __hash__(self):
        return hash(None)

    def __eq__(self, other):
        "Only equal to things of zero length"
        if isinstance(other, (Empty, Undefined)):
            return True
        if not hasattr(other, "__len__"):
            return False
        return len(other) == 0

    def eval(self, ctx):
        return self


class PushResult(Node):
    "Special node class used to push results for PredicateSets"
    def __init__(self, predicate, ast):
        self.pred = predicate
        self.left = ast

    def __deepcopy__(self, memo=None):
        # Do not copy the predicate
        return PushResult(self.pred, dup(self.left))

    def name(self):
        return "PushResult of '%s'" % self.pred.predicate

    @failure_info
    def eval(self, ctx):
        ctx.reach += 1
        if self.left.eval(ctx):
            ctx.pred.push_match(self.pred)
            return True
        return False

    def failure_info(self, ctx):
        err = "Predicate '%s' failed to match" % self.pred.predicate
        ctx.failed.append(err)


class Branch(Node):
    """
    Special node class used for Predicate Sets.
    The branch node allows for an AST node to be evaluated,
    and if True to take the left branch, otherwise to evaluate
    the right branch. This allows for a single evaluation
    of a term to prune other unnecessary checks.
    """
    def __init__(self, expr, left, right):
        self.expr = expr
        self.left = left
        self.right = right

    def name(self):
        return "Branch on %s" % self.expr.name()

    def description(self, buf=None, depth=0, max_depth=0):
        """
        Provides a human readable tree description
        """
        if not buf:
            buf = ""
        pad = depth * "\t"
        if max_depth and depth == max_depth:
            buf += pad + "...\n"
            return buf

        buf += pad + self.name() + "\n"
        buf = self.expr.description(buf, depth+1, max_depth+2)
        if hasattr(self, "left"):
            buf = self.left.description(buf, depth+1, max_depth)
        if hasattr(self, "right"):
            buf = self.right.description(buf, depth+1, max_depth)
        return buf

    @failure_info
    def eval(self, ctx):
        # Evaluate the expression first
        res = self.expr.eval(ctx)

        # Branch on the expression
        if res and self.left:
            return self.left.eval(ctx)
        elif self.right:
            return self.right.eval(ctx)
        return False

    def failure_info(self, ctx):
        with ctx:
            res = self.expr.eval(ctx)
        if res:
            err = "Left hand side (True) of " + self.name() + " failed"
        else:
            err = "Right hand side (False) of " + self.name() + " failed"
        ctx.failed.append(err)


class Both(Node):
    """
    Special node class used for merging predicates.
    This node allows for all possible sub-trees to
    be evalauted and evaluates to True if any child did.

    It is used instead of OR trees since it does not
    short-circuit the evaluation.
    """
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def name(self):
        "Provides human name with location"
        return self.__class__.__name__

    @failure_info
    def eval(self, ctx):
        l = self.left.eval(ctx)
        r = self.right.eval(ctx)
        return l or r

    def failure_info(self, ctx):
        err = "Both sides of " + self.name() + " failed"
        ctx.failed.append(err)


class CachedNode(Node):
    """
    Special node class that is used to avoid re-computing
    values if they are already cached. This is used when
    predicates are merged and share expressions that are
    not refactored into a branch.
    """
    def __init__(self, left, cache_id):
        self.expr = left
        self.cache_id = cache_id

    def name(self):
        return "Cache of " + self.expr.name()

    def description(self, buf=None, depth=0, max_depth=0):
        """
        Provides a human readable tree description
        """
        if not buf:
            buf = ""
        pad = depth * "\t"
        if max_depth and depth == max_depth:
            buf += pad + "...\n"
            return buf

        buf += pad + self.name() + "\n"
        buf = self.expr.description(buf, depth+1, max_depth+2)
        return buf

    def eval(self, ctx):
        # Check the cache
        cached_res = ctx.cached_res.get(self.cache_id, None)
        if cached_res is not None:
            ctx.cache_hits += 1
            if ctx.analyze and not cached_res:
                self.failure_info(ctx)
            return cached_res

        # Evaluate
        ctx.cache_misses += 1
        l = self.expr.eval(ctx)

        # Cache the result
        ctx.cached_res[self.cache_id] = l
        return l

    def failure_info(self, ctx):
        if hasattr(self.expr, "failure_info"):
            self.expr.failure_info(ctx)


class LiteralSet(Node):
    """
    This node represents a 'set' of values. It is constructed
    as a literal in the predicate and is used for things like
    contains.
    """
    static = False
    static_val = None

    def __init__(self, value):
        self.value = frozenset(value)

    def name(self):
        return "Set of %s" % repr(self.value)

    def static_resolve(self, pred):
        "Uses the predicate to perform a static resolution"
        static = True
        static_val = set([])

        # Check if each item is static
        for item in self.value:
            # Only check literal, since Number and Constant
            # are always static
            if isinstance(item, Literal):
                item.static_resolve(pred)
                if item.static:
                    static_val.add(item.static_val)
                else:
                    static = False
            else:
                static_val.add(item.value)


        # If all items are static, so are we
        if static:
            self.static = True
            self.static_val = static_val

    def __bool__(self):
        "Acts like False"
        return len(self.value) > 0

    # Python 2 legacy
    def __nonzero__(self):
        "Acts like False."
        return False

    def __contains__(self, o):
        return o in self.value

    def __eq__(self, other):
        if len(self.value) == 0 and isinstance(other, (Undefined, Empty)):
            return True
        elif isinstance(other, LiteralSet):
            return self.value == other.value
        elif isinstance(other, set):
            return self.value == other
        elif isinstance(other, list):
            return self.value == set(other)
        else:
            return False

    def eval(self, ctx):
        # Static sets are easy
        if self.static:
            return self.static_val

        # Non-static set requires resolution of each literal value
        s = set([])
        for i in self.value:
            if isinstance(i, Literal):
                v = i.eval(ctx)
            else:
                v = i.value
            s.add(v)
        return frozenset(s)

