from parser import get_lexer, get_parser
import ast

class InvalidPredicate(Exception):
    "Raised for evaluation of an invalid predicate"
    pass


class Predicate(object):
    """
    This class provides a convenient interface for parsing and
    evaluating predicates. It is the recommended way of using PyPred.

    Sub-classes may be interested in overriding the behavior of
    resolve_identifier to change the evaluation of the predicate.
    """
    def __init__(self, predicate, debug=0):
        "Initializes the Predicate object with the string predicate."
        # Validate the predicate
        if not isinstance(predicate, str):
            raise TypeError("Predicate must be a string!")
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
            self.ast_errors = {"errors": [], "regex": {}}
        except Exception, e:
            self.ast = None
            self.ast_validated = True
            self.ast_valid = False
            self.ast_errors = {"errors": [str(e)], "regex": {}}

    def is_valid(self):
        "Checks if the predicate is valid"
        self.ast_validated = True
        if self.lexer_errors:
            return False
        if self.parser_errors:
            return False
        if not self.ast:
            return False
        if self.ast_validated:
            return self.ast_valid

        # Valid the AST once
        self.ast_valid, self.ast_errors = self.ast.validate()
        return self.ast_valid

    def parse_errors(self):
        "Returns all the errors if the predicate is not valid"
        # Clone the ast errors
        info = dict(self.ast_errors)

        # Merge all the errors in order
        info["errors"] = self.lexer_errors + self.parser_errors + list(info["errors"])
        return info

    def evaluate(self, document):
        "Evaluates the predicate against the document"
        # Use analyze and throw away the info
        result, _ = self.analyze(document)
        return result

    def analyze(self, document):
        """
        Evaluates a predicate against the input document,
        while trying to provide additional information about
        the cause of failure
        """
        if not self.is_valid():
            raise InvalidPredicate

        return self.ast.evaluate(self, document)

    def resolve_identifier(self, document, identifier):
        """
        Resolves string literal identifiers in the scope of
        the document while evaluating the predicate. Sub-classes
        can override this to change the default behavior.
        """
        # Treat anything that is quoted as a string literal
        if identifier[0] == identifier[-1] and identifier[0] in ("'", "\""):
            return identifier.strip(identifier[0])

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

        # Return the undefined node if all else fails
        return ast.Undefined()

