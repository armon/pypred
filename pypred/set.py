"""
This module provides implementations of Predicate Sets.
A predicate set is a collection of predicates that are
all evaluated against a single input to find all matching
predicates. It provides both a naive implementation that
sequentially evaluates predicates, as well as an optimizing
implementation.
"""
from .merge import merge, refactor
from .predicate import LiteralResolver
from . import ast


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
        self.update([p])

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
    def __init__(self, preds=None, settings=None):
        LiteralResolver.__init__(self)
        self.settings = settings
        self.predicates = set([])
        self.ast = None
        self.finalized = False
        if preds:
            self.update(preds)

    def add(self, p):
        """
        Updates the set with a new predicate. This will invalidate
        the current AST. It is not recommended to interleave add/evaluate.
        """
        self.update([p])

    def update(self, preds):
        "Update the set with a union of the new predicates"
        if self.finalized:
            raise Exception("Cannot alter a finalized set!")

        for p in preds:
            if not p.is_valid():
                raise ValueError("Invalid predicate provided!")

        old_l = len(self.predicates)
        self.predicates.update(preds)
        if len(self.predicates) != old_l:
            self.ast = None

    def description(self, max_depth=0):
        "Provides a tree like human readable description of the predicate"
        if self.ast is None:
            self.compile_ast()
        return self.ast.description(max_depth=max_depth)

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

    def analyze(self, document):
        """
        Evaluates a predicate against the input document,
        while trying to provide additional information about
        the cause of failure. This is generally much slower
        that using the equivilent `evaluate`.

        Returns a tuple of (Result, Matches, Ctx).
        Result is a boolean, Matches a list of predices
        and ctx is the evaluation context, containing among other
        things the failure reasons and all of the literal resolution values.
        The failed attribute has all the failure reasons in order.
        The literals attribute contains the resolved values for all literals.
        """
        if self.ast is None:
            self.compile_ast()

        # Set the results array so that the ast can push the matches
        results = []
        self._results = results

        # Analyze
        res, ctx = self.ast.analyze(self, document)

        # Reset the results array and return this instance
        self._results = None
        return res, results, ctx

    def compile_ast(self):
        """
        Forces compilation of the internal ast tree.
        This must be done after any changes to the set of
        predicates.
        """
        if self.finalized:
            raise Exception("Cannot compile a finalized set!")
        if self.predicates:
            merged = merge(list(self.predicates))
            self.ast = refactor(self, merged, self.settings)
        else:
            self.ast = ast.Constant(True)

    def push_match(self, match):
        """
        This method is only to be invoked by the AST tree
        to push results during an evaluation.
        """
        self._results.append(match)

    def finalize(self):
        """
        This method can be invoked to 'finalize'. Once
        this is done, the set cannot be altered. However,
        lots of extraneous data can be purged to save memory.

        This WILL clear the predicate string and AST from all
        input predicates. Use only with caution.
        """
        # Ensure the AST if compiled first
        if self.ast is None:
            self.compile_ast()

        # Clear the sub-AST's and string predicates
        for p in self.predicates:
            p.predicate = None
            p.ast = None

        # Remove our set, the AST has it
        self.predicates = None

        # Set as finalized
        self.finalized = True

