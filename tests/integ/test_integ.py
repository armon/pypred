"""
This module performs some integration tests by
using a seperate preds.txt file. Each line is
treated as a predicate and is evaluated in a
predefined context
"""
import os
import os.path
from pypred import Predicate

DOC = {
    "name": "Jack",
    "friend": "Jill",
    "server": "east-web-001",
    "load": 1.1,
    "errors": ["disk full", "cpu load"],
    "status": 500,
    "nested": {"source": "twitter", "tweet": {"text": "I love coffee!"}},
}


def test_samples():
    p = os.path.dirname(os.path.abspath(__file__))
    fh = open(os.path.join(p, "preds.txt"))
    for line, pred in enumerate(fh):
        pred = pred.strip()
        obj = Predicate(pred)
        assert obj.is_valid(), pred
        res, info = obj.analyze(DOC)

        if not pred.endswith("true") and not pred.endswith("false"):
            print "Line: ", line
            print "Unknown result!"
            print "Predicate: ", pred
            assert False

        if (pred.endswith("true") and not res) or (pred.endswith("false") and res):
            print "Line: ", line
            print "Predicate: ", pred
            print "Failures: ", "\n".join(info["failed"])
            print "Literals: "
            for k, v in info["literals"].iteritems():
                print "\t%s : %s" % (k, repr(v))
            assert False

