"""
This module provides implementations of Predicate Sets.
A predicate set is a collection of predicates that are
all evaluated against a single input to find all matching
predicates. It provides both a naive implementation that
sequentially evaluates predicates, as well as an optimizing
implementation.
"""
from merge import merge
from predicate import LiteralResolver


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


class OptimizedPredicateSet(LiteralResolver):
    """
    This class implements an optimizing predicate set.
    Internally, the predicates are rewritten and merged
    into a single AST that can be evaluated in a single pass.
    """
    def __init__(self, preds=None):
        LiteralResolver.__init__(self)
        self.predicates = set([])
        self.ast = None
        if preds:
            self.update(preds)

    def add(self, p):
        """
        Updates the set with a new predicate. This will invalidate
        the current AST. It is not recommended to interleave add/evaluate.
        """
        if not p.is_valid():
            raise ValueError("Invalid predicate provided!")

        # Add and check if we need to invalidate the ast
        old_l = len(self.predicates)
        self.predicates.add(p)
        if len(self.predicates) != old_l:
            self.ast = None

    def update(self, preds):
        "Update the set with a union of the new predicates"
        for p in preds:
            if not p.is_valid():
                raise ValueError("Invalid predicate provided!")

        old_l = len(self.predicates)
        self.predicates.update(preds)
        if len(self.predicates) != old_l:
            self.ast = None

    def evaluate(self, doc):
        """
        Evaluates the predicates against the document.
        Returns a list of matching predicates
        """
        if self.ast is None:
            self.compile_ast()

        # Set the results array so that the ast can push the matches
        results = []
        self._results = results

        # Evaluate
        self.ast.evaluate(self, doc)

        # Reset the results array and return this instance
        self._results = None
        return results

    def compile_ast(self):
        """
        Forces compilation of the internal ast tree.
        This must be done after any changes to the set of
        predicates.
        """
        self.ast = merge(list(self.predicates))

    def push_match(self, match):
        """
        This method is only to be invoked by the AST tree
        to push results during an evaluation.
        """
        self._results.append(match)

