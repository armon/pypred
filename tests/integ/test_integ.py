"""
This module performs some integration tests by
using a seperate preds.txt file. Each line is
treated as a predicate and is evaluated in a
predefined context
"""
import os
import os.path
from pypred import Predicate
from . import DOC


def test_samples():
    p = os.path.dirname(os.path.abspath(__file__))
    fh = open(os.path.join(p, "preds.txt"))
    for line, pred in enumerate(fh):
        pred = pred.strip()
        obj = Predicate(pred)
        if not obj.is_valid():
            print("Invalid Predicate!")
            print("Line: ", line)
            print("Predicate: ", pred)
            info = obj.errors()
            print("Errors: ", "\n".join(info["errors"]))
            for k, v in list(info["regex"].items()):
                print("\t%s : %s" % (k, repr(v)))
            assert False

        res, ctx = obj.analyze(DOC)
        if not pred.endswith("true") and not pred.endswith("false"):
            print("Line: ", line)
            print("Unknown result!")
            print("Predicate: ", pred)
            assert False

        if (pred.endswith("true") and not res) or (pred.endswith("false") and res):
            print("Line: ", line)
            print("Predicate: ", pred)
            print("Failures: ", "\n".join(ctx.failed))
            print("Literals: ")
            for k, v in list(ctx.literals.items()):
                print("\t%s : %s" % (k, repr(v)))
            assert False

