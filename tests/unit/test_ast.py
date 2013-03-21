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
        assert "must be a string" in info["errors"][0]

    def test_bad_regex(self):
        a = ast.Regex("(abc")
        valid, info = a.validate()
        assert not valid
        assert "Compilation failed" in info["errors"][0]
        assert "(abc" in info["regex"]
        assert info["regex"]["(abc"] == "unbalanced parenthesis"

    def test_bad_regex_inp(self):
        a = self.ast("foo matches '(abc'")
        valid, info = a.validate()
        assert not valid
        assert "Compilation failed" in info["errors"][0]
        assert "(abc" in info["regex"]
        assert info["regex"]["(abc"] == "unbalanced parenthesis"

    def test_match_bad_arg(self):
        a = ast.MatchOperator(ast.Literal("foo"), ast.Literal("bar"))
        valid, info = a.validate()
        assert not valid
        assert "must take a regex" in info["errors"][0]

    def test_contains_bad(self):
        a = ast.ContainsOperator(ast.Literal("foo"), ast.Empty())
        valid, info = a.validate()
        assert not valid
        assert "Contains operator must take" in info["errors"][0]

    def test_contains_valid_args(self):
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
        if type == "!=":
            assert res
        else:
            assert not res
        if not res:
            assert ("%s comparison at" % type.upper()) in info["failed"][0]
        assert info["literals"]["l"] == d["l"]
        assert info["literals"]["r"] == ast.Undefined()

    @pytest.mark.parametrize(("type",), [
        (">=",), (">",), ("<",), ("<=",), ("=",), ("!=",), ("is",)])
    def test_compare_empty(self, type):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.CompareOperator(type, l, r)
        d = {"l": 1, "r": ast.Empty()}
        res, info = a.analyze(MockPred(), d)

        # Determine the expected result
        if type == "!=":
            assert res
        else:
            assert not res
        if not res:
            assert ("%s comparison at" % type.upper()) in info["failed"][0]
        assert info["literals"]["l"] == d["l"]
        assert info["literals"]["r"] == ast.Empty()

    def test_contains_invalid(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.ContainsOperator(l, r)
        d = {"l": 1, "r": None}
        res, info = a.analyze(MockPred(), d)
        assert not res
        assert "does not support contains" in info["failed"][0]
        assert info["literals"]["l"] == 1
        assert "r" not in info["literals"]

    def test_contains_undef(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.ContainsOperator(l, r)
        d = {"r": 5}
        res, info = a.analyze(MockPred(), d)
        assert not res
        assert "not in left side" in info["failed"][0]
        assert info["literals"]["l"] == ast.Undefined()
        assert info["literals"]["r"] == 5

    def test_contains_empty(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.ContainsOperator(l, r)
        d = {"l": [], "r": 5}
        res, info = a.analyze(MockPred(), d)
        assert not res
        assert "not in left side" in info["failed"][0]
        assert info["literals"]["l"] == []
        assert info["literals"]["r"] == 5

    def test_contains_valid(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.ContainsOperator(l, r)
        d = {"l": [42], "r": 42}
        res, info = a.analyze(MockPred(), d)
        assert res
        assert info["literals"]["l"] == [42]
        assert info["literals"]["r"] == 42

    def test_match_bad_types(self):
        l = ast.Literal("l")
        r = ast.Regex(ast.Literal('abcd'))
        a = ast.MatchOperator(l, r)
        d = {"l": 42}
        res, info = a.analyze(MockPred(), d)
        assert not res
        assert "not a string" in info["failed"][0]
        assert info["literals"]["l"] == 42

    def test_match_undef(self):
        l = ast.Literal("l")
        r = ast.Regex(ast.Literal('abcd'))
        a = ast.MatchOperator(l, r)
        d = {}
        res, info = a.analyze(MockPred(), d)
        assert not res
        assert "not a string" in info["failed"][0]
        assert info["literals"]["l"] == ast.Undefined()

    def test_match_no_match(self):
        l = ast.Literal("l")
        r = ast.Regex(ast.Literal('abcd'))
        a = ast.MatchOperator(l, r)
        d = {"l": "tubez"}
        res, info = a.analyze(MockPred(), d)
        assert not res
        assert "does not match" in info["failed"][0]
        assert info["literals"]["l"] == "tubez"

    def test_match(self):
        l = ast.Literal("l")
        r = ast.Regex(ast.Literal('abcd'))
        a = ast.MatchOperator(l, r)
        d = {"l": "abcd"}
        res, info = a.analyze(MockPred(), d)
        assert res
        assert info["literals"]["l"] == "abcd"

    def test_push(self):
        p = ast.PushResults([True, False])
        class TestSet(object):
            def __init__(self):
                self.res = []
            def push_matches(self, matches):
                self.res.extend(matches)

        testset = TestSet()
        assert p.eval(testset, {}, None)
        assert testset.res == [True, False]

    def test_branch(self):
        l = ast.Literal('a')
        r = ast.Literal('b')
        check = ast.CompareOperator('>', l, r)
        true = ast.Constant(True)
        false = ast.Constant(False)
        b = ast.Branch(check, true, false)

        assert b.eval(MockPred(), {'a': 2, 'b':1})

        res, info = b.analyze(MockPred(), {'a': 1, 'b':2})
        assert not res
        assert info["literals"]["a"] == 1
        assert info["literals"]["b"] == 2
        assert info["failed"][-1].startswith("Right hand side")

