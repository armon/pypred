"""
Unit tests for the lexer
"""
import pytest
from pypred import parser, ast

class MockPred(object):
    def resolve_identifier(self, doc, ident):
        if ident in doc:
            return doc[ident]
        else:
            return ast.Undefined()


class TestAST(object):
    def ast(self, inp):
        lexer = parser.get_lexer()
        p = parser.get_parser(lexer=lexer)
        return p.parse(inp, lexer=lexer)

    def test_jack_and_jill(self):
        a = self.ast("name is Jack and friend_name is Jill")
        valid, info = a.validate()
        assert valid

    def test_bad_number(self):
        a = ast.Number("0..0")
        valid, info = a.validate()
        assert not valid
        assert "Failed to convert" in info["errors"][0]

    def test_bad_constant(self):
        a = ast.Constant(42)
        valid, info = a.validate()
        assert not valid
        assert "Invalid Constant" in info["errors"][0]

    def test_bad_regex_type(self):
        a = ast.Regex(42)
        valid, info = a.validate()
        assert not valid
        assert "Regex must be a string" in info["errors"][0]

    def test_bad_regex(self):
        a = ast.Regex("(abc")
        valid, info = a.validate()
        assert not valid
        assert "Regex compilation failed" in info["errors"][0]
        assert "(abc" in info["regex"]
        assert info["regex"]["(abc"] == "unbalanced parenthesis"

    def test_bad_regex_inp(self):
        a = self.ast("foo matches '(abc'")
        valid, info = a.validate()
        assert not valid
        assert "Regex compilation failed" in info["errors"][0]
        assert "(abc" in info["regex"]
        assert info["regex"]["(abc"] == "unbalanced parenthesis"

    def test_match_bad_arg(self):
        a = ast.MatchOperator(ast.Literal("foo"), ast.Literal("bar"))
        valid, info = a.validate()
        assert not valid
        assert "Match operator must take a regex" in info["errors"][0]

    def test_contains_bad(self):
        a = ast.ContainsOperator(ast.Literal("foo"), ast.Empty())
        valid, info = a.validate()
        assert not valid
        assert "Contains operator must take" in info["errors"][0]

    def test_contains_valid(self):
        a = ast.ContainsOperator(ast.Literal("foo"), ast.Literal("bar"))
        valid, info = a.validate()
        assert valid

    def test_bad_compare(self):
        a = ast.CompareOperator("!", ast.Literal("foo"), ast.Empty())
        valid, info = a.validate()
        assert not valid
        assert "Unknown compare" in info["errors"][0]

    def test_bad_logic(self):
        a = ast.LogicalOperator("!", ast.Literal("foo"), ast.Empty())
        valid, info = a.validate()
        assert not valid
        assert "Unknown logical" in info["errors"][0]

    def test_bad_child(self):
        c = ast.CompareOperator("!", ast.Literal("foo"), ast.Empty())
        a = ast.LogicalOperator("and", ast.Literal("foo"), c)
        valid, info = a.validate()
        assert not valid
        assert "Unknown compare" in info["errors"][0]

    def test_logical_eval1(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.LogicalOperator('and', l, r)
        res, info = a.analyze(MockPred(), {"l": True, "r": False})
        assert not res
        assert info["literals"]["l"] == True
        assert info["literals"]["r"] == False
        assert "Right hand side of AND operator at" in info["failed"][0]

    def test_logical_eval2(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.LogicalOperator('and', l, r)
        res, info = a.analyze(MockPred(), {"l": True, "r": True})
        assert res
        assert info["literals"]["l"] == True
        assert info["literals"]["r"] == True

    def test_logical_eval3(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.LogicalOperator('or', l, r)
        res, info = a.analyze(MockPred(), {"l": False, "r": False})
        assert not res
        assert info["literals"]["l"] == False
        assert info["literals"]["r"] == False
        assert "Both sides of OR operator at" in info["failed"][0]

    def test_logical_eval4(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.LogicalOperator('or', l, r)
        res, info = a.analyze(MockPred(), {"l": False, "r": True})
        assert res
        assert info["literals"]["l"] == False
        assert info["literals"]["r"] == True

    def test_logical_eval5(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.LogicalOperator('or', l, r)
        res, info = a.analyze(MockPred(), {"l": False})
        assert not res
        assert info["literals"]["l"] == False
        assert info["literals"]["r"] == ast.Undefined()
        assert "Both sides of OR operator" in info["failed"][0]

    def test_logical_eval6(self):
        "Short circuit logic"
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.LogicalOperator('or', l, r)
        res, info = a.analyze(MockPred(), {"l": True})
        assert res
        assert info["literals"]["l"] == True
        assert "r" not in info["literals"]

    def test_logical_eval7(self):
        "Short circuit logic"
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.LogicalOperator('and', l, r)
        res, info = a.analyze(MockPred(), {"l": False})
        assert not res
        assert info["literals"]["l"] == False
        assert "r" not in info["literals"]
        assert "Left hand side" in info["failed"][0]

    def test_negate_false(self):
        l = ast.Literal("l")
        a = ast.NegateOperator(l)
        res, info = a.analyze(MockPred(), {"l": False})
        assert res
        assert info["literals"]["l"] == False

    def test_negate_true(self):
        l = ast.Literal("l")
        a = ast.NegateOperator(l)
        res, info = a.analyze(MockPred(), {"l": True})
        assert not res
        assert info["literals"]["l"] == True

    @pytest.mark.parametrize(("type",), [
        (">=",), (">",), ("<",), ("<=",), ("=",), ("!=",), ("is",)])
    def test_compare(self, type):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.CompareOperator(type, l, r)
        d = {"l": 1, "r": 5}
        res, info = a.analyze(MockPred(), d)

        # Determine the expected result
        if type == "=":
            s = '%d %s %d' % (d["l"], "==", d["r"])
        else:
            s = '%d %s %d' % (d["l"], type, d["r"])
        expected = eval(s)

        assert res == expected
        if not res:
            assert ("%s comparison at" % type.upper()) in info["failed"][0]
        assert info["literals"]["l"] == d["l"]
        assert info["literals"]["r"] == d["r"]

    @pytest.mark.parametrize(("type",), [
        (">=",), (">",), ("<",), ("<=",), ("=",), ("!=",), ("is",)])
    def test_compare_undef(self, type):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.CompareOperator(type, l, r)
        d = {"l": 1}
        res, info = a.analyze(MockPred(), d)

        # Determine the expected result
        if type == "=":
            s = '%d %s %d' % (d["l"], "==", d["r"])
        else:
            s = '%d %s %d' % (d["l"], type, d["r"])
        expected = eval(s)

        assert res == expected
        if not res:
            assert ("%s comparison at" % type.upper()) in info["failed"][0]
        assert info["literals"]["l"] == d["l"]
        assert info["literals"]["r"] == ast.Undefined()

