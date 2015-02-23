from .parser import get_lexer, get_parser
from . import ast
import collections

# python2/3 basestring compatibility
try:
    unicode = unicode
except NameError: # python3
    basestring = (str, bytes)

class InvalidPredicate(Exception):
    "Raised for evaluation of an invalid predicate"
    pass


class LiteralResolver(object):
    "Mixin to provide literal resolution"
    def __init__(self):
        self.resolvers = {}

    def set_resolver(self, identifier, relv):
        """
        Sets a custom resolver. If resolve_identifier cannot
        find the identifier in the document, and there is a matching
        resolver, that resolver will be used. If the resolver is
        callable, it will be invoked, otherwise it is returned as is.
        """
        self.resolvers[identifier] = relv

    def static_resolve(self, identifier):
        """
        Resolves a string literal identifier statically
        in the absense of a document. This can return undefined
        if not possible. This is used for optimizing predicates.
        """
        # Treat anything that is quoted as a string literal
        if identifier[0] == identifier[-1] and identifier[0] in ("'", "\""):
            return identifier[1:-1]

        return ast.Undefined()

    def resolve_identifier(self, document, identifier):
        """
        Resolves string literal identifiers in the scope of
        the document while evaluating the predicate. Sub-classes
        can override this to change the default behavior.
        """
        # Treat anything that is quoted as a string literal
        if identifier[0] == identifier[-1] and identifier[0] in ("'", "\""):
            return identifier[1:-1]

        # Check for the identifier in the document
        if identifier in document:
            return document[identifier]

        # Allow the dot syntax for nested object lookup
        # i.e. req.sdk.version = req["sdk"]["version"]
        if "." in identifier:
            parts = identifier.split(".")
            found = True
            root = document
            for p in parts:
                if p in root:
                    root = root[p]
                else:
                    found = False
                    break
            if found:
                return root

        # Check if there is a resolver
        if identifier in self.resolvers:
            relv = self.resolvers[identifier]
            if isinstance(relv, collections.Callable):
                return relv()
            else:
                return relv

        # Return the undefined node if all else fails
        return ast.Undefined()


class Predicate(LiteralResolver):
    """
    This class provides a convenient interface for parsing and
    evaluating predicates. It is the recommended way of using PyPred.

    Sub-classes may be interested in overriding the behavior of
    resolve_identifier to change the evaluation of the predicate.
    """
    def __init__(self, predicate, debug=0):
        """
        Initializes the Predicate object with the string predicate.

        Arguments:
            predicate : String predicate
            debug : optional, defaults to 0. Controls the debug behavior
             of the underlying parser and lexer.

        Returns:
            Predicate object
        """
        # Validate the predicate
        if not isinstance(predicate, basestring):
            raise TypeError("Predicate must be a string!")

        # Initialize the literal resolver
        LiteralResolver.__init__(self)

        # Store the predicate
        self.predicate = predicate

        # Setup the lexer
        lexer = get_lexer()
        self.lexer_errors = lexer.errors

        # Setup the parser
        p = get_parser(lexer=lexer, debug=debug)
        self.parser_errors = p.errors

        # Try to get the AST tree
        try:
            self.ast = p.parse(self.predicate, lexer=lexer)
            self.ast_validated = False
            self.ast_valid = False
            self.ast_errors = None
        except (Exception) as e:
            self.ast = None
            self.ast_validated = True
            self.ast_valid = False
            self.ast_errors = {"errors": [str(e)], "regex": {}}

        # Clear the error lists if empty
        if not self.lexer_errors:
            self.lexer_errors = None
        if not self.parser_errors:
            self.parser_errors = None

    def is_valid(self):
        "Checks if the predicate is valid"
        if self.ast_validated:
            return self.ast_valid
        if self.lexer_errors:
            return False
        if self.parser_errors:
            return False
        if not self.ast:
            return False

        # Valid the AST once
        self.ast_validated = True
        self.ast_valid, self.ast_errors = self.ast.validate()
        if self.ast_valid:
            self.ast_errors = None
        return self.ast_valid

    def errors(self):
        "Returns a list of all the errors if the predicate is not valid"
        errors = []

        # Add the lexer errors in a friendly way
        if self.lexer_errors:
            for char, pos, line in self.lexer_errors:
                e = "Failed to parse characters %s at line %d, col %d" % \
                        (char, pos, line)
                errors.append(e)

        # Add the parser errors in a friendly way
        if self.parser_errors:
            for err in self.parser_errors:
                if isinstance(err, tuple) and len(err) == 5:
                    _, _, val, pos, line = err
                    e = "Syntax error with %s at line %d, col %d" % \
                        (val, pos, line)
                    errors.append(e)
                elif isinstance(err, str):
                    errors.append(err)
                else:
                    errors.append(repr(err))

        # Copy the ast errors
        if self.ast_errors:
            for err in self.ast_errors["errors"]:
                errors.append(err)

        # Build info dict
        info = {
            "errors": errors,
            "regex": self.ast_errors["regex"] if self.ast_errors else []
        }
        return info

    def description(self, max_depth=0):
        "Provides a tree like human readable description of the predicate"
        if not self.is_valid():
            raise InvalidPredicate
        return self.ast.description(max_depth=max_depth)

    def evaluate(self, document):
        "Evaluates the predicate against the document."
        if not self.is_valid():
            raise InvalidPredicate
        return self.ast.evaluate(self, document)

    def analyze(self, document):
        """
        Evaluates a predicate against the input document,
        while trying to provide additional information about
        the cause of failure. This is generally much slower
        that using the equivilent `evaluate`.

        Returns a tuple of (Result, Ctx).
        Result is a boolean, and ctx is the evaluation context, containing among other
        things the failure reasons and all of the literal resolution values.
        The failed attribute has all the failure reasons in order.
        The literals attribute contains the resolved values for all literals.
        """
        if not self.is_valid():
            raise InvalidPredicate
        return self.ast.analyze(self, document)

