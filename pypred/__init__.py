__version__ = "0.2.2"

from merge import RefactorSettings
from predicate import Predicate, InvalidPredicate
from set import PredicateSet, OptimizedPredicateSet

__all__ = [
    "Predicate",
    "InvalidPredicate",
    "PredicateSet",
    "OptimizedPredicateSet",
    "RefactorSettings"
]

