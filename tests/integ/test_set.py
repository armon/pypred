"""
This module performs some integration tests by
using a seperate preds.txt file. Each line is
treated as a predicate and is evaluated as part
of a predicate set.
"""
import os
import os.path
from pypred import Predicate, PredicateSet, OptimizedPredicateSet


DOC = {
    "name": "Jack",
    "friend": "Jill",
    "server": "east-web-001",
    "load": 1.1,
    "errors": ["disk full", "cpu load"],
    "status": 500,
    "nested": {"source": "twitter", "tweet": {"text": "I love coffee!"}},
    "val": 100,
    "val2": 200,
}


def test_samples():
    p = os.path.dirname(os.path.abspath(__file__))
    fh = open(os.path.join(p, "preds.txt"))
    s1 = PredicateSet()
    s2 = OptimizedPredicateSet()

    match = []
    for line, pred in enumerate(fh):
        pred = pred.strip()
        obj = Predicate(pred)

        # Add to the set
        s1.add(obj)
        s2.add(obj)

        # Add to the list of matches
        if pred.endswith("true"):
            match.append(pred)

    # Run the sets
    s1_match = s1.evaluate(DOC)
    s2_match = s2.evaluate(DOC)

    # Ensure both match
    match.sort()
    s1_match = [p.predicate for p in s1_match]
    s1_match.sort()
    s2_match = [p.predicate for p in s2_match]
    s2_match.sort()
    assert s1_match == match
    assert s2_match == match

