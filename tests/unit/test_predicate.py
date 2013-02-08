"""
Unit tests for the lexer
"""
from pypred import Predicate

class TestPredicate(object):
    def test_jack_and_jill(self):
        p = Predicate("name is 'Jack' and friend is 'Jill'")
        assert p.is_valid()
        assert p.evaluate({"name": "Jack", "friend": "Jill"})
        res, info = p.analyze({"name": "Jack", "friend": "Jill"})
        assert res

