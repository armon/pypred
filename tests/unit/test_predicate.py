"""
Unit tests for the lexer
"""
from pypred import Predicate, ast

class TestPredicate(object):
    def test_jack_and_jill(self):
        p = Predicate("name is 'Jack' and friend is 'Jill'")
        assert p.is_valid()
        assert p.evaluate({"name": "Jack", "friend": "Jill"})
        res, info = p.analyze({"name": "Jack", "friend": "Jill"})
        assert res
        assert p.description() == """AND operator at line: 1, col 15
	IS comparison at line: 1, col 5
		Literal name at line: 1, col 0
		Literal 'Jack' at line: 1, col 8
	IS comparison at line: 1, col 26
		Literal friend at line: 1, col 19
		Literal 'Jill' at line: 1, col 29
"""

    def test_invalid_end(self):
        p = Predicate("name is 'Jack' and ")
        assert not p.is_valid()
        assert 'Unexpected end of predicate!' in p.errors()["errors"]

    def test_invalid_token(self):
        p = Predicate("name is !! and true")
        assert not p.is_valid()
        assert 'Failed to parse characters !!' in p.errors()["errors"][0]

    def test_invalid_parse(self):
        p = Predicate("true true")
        assert not p.is_valid()
        assert 'Syntax error with true' in p.errors()["errors"][0]

    def test_invalid_ast(self):
        p = Predicate("server matches '(unbal'")
        assert not p.is_valid()
        errs = p.errors()
        assert 'Compilation failed for' in errs["errors"][0]
        assert 'unbalanced parenthesis' == errs["regex"]["(unbal"]

    def test_resolve_missing(self):
        p = Predicate("name is 'Jack' and friend is 'Jill'")
        assert p.resolve_identifier({}, "name") == ast.Undefined()

    def test_resolve_present(self):
        p = Predicate("name is 'Jack' and friend is 'Jill'")
        assert p.resolve_identifier({"name": "abc"}, "name") == "abc"

    def test_resolve_dotsyntax(self):
        p = Predicate("name is 'Jack' and friend is 'Jill'")
        doc = {
            "sub": {
                "inner": {
                    "val" : 42
                }
            }
        }
        assert p.resolve_identifier(doc, "sub.inner.val") == 42

    def test_resolve_quote(self):
        p = Predicate("name is 'Jack' and friend is 'Jill'")
        assert p.resolve_identifier({}, "'name'") == "name"
        assert p.resolve_identifier({}, "\"name\"") == "name"

    def test_resolve_custom(self):
        import random
        p = Predicate("name is 'Jack' and friend is 'Jill'")
        p.set_resolver("random", random.random)
        r1 = p.resolve_identifier({}, "random")
        r2 = p.resolve_identifier({}, "random")
        assert r1 != r2

    def test_resolve_custom_fixed(self):
        p = Predicate("name is 'Jack' and friend is 'Jill'")
        p.set_resolver("answer", 42)
        r1 = p.resolve_identifier({}, "answer")
        assert r1 == 42

