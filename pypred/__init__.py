__version__ = "0.1.0"

try:
    from parser import get_lexer, get_parser
    import ast
    from predicate import Predicate, InvalidPredicate
    __all__ = ["get_lexer", "get_parser", "ast", "Predicate", "InvalidPredicate"]
except ImportError:
    print "Missing dependencies!"
    __all__ = []

