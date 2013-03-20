"""
This module provides implementations of Predicate Sets.
A predicate set is a collection of predicates that are
all evaluated against a single input to find all matching
predicates. It provides both a naive implementation that
sequentially evaluates predicates, as well as an optimizing
implementation.
"""

class PredicateSet(object):
    """
    This class implements a naive predicate set. It provides
    no optimizations and does a sequential evaluation of
    each predicate.
    """
    def __init__(self, preds=None):
        self.predicates = set([])
        if preds:
            self.update(preds)

    def add(self, p):
        "Updates the set with a new predicate"
        if not p.is_valid():
            raise ValueError("Invalid predicate provided!")
        self.predicates.add(p)

    def update(self, preds):
        "Update the set with a union of the new predicates"
        for p in preds:
            if not p.is_valid():
                raise ValueError("Invalid predicate provided!")
        self.predicates.update(preds)

    def evaluate(self, doc):
        """
        Evaluates the predicates against the document.
        Returns a list of matching predicates
        """
        match = []
        for p in self.predicates:
            if p.evaluate(doc):
                match.append(p)
        return match

