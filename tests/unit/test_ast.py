"""
Unit tests for the lexer
"""
import pytest
from pypred import parser, ast

class MockPred(object):
    def static_resolve(self, identifier):
        if identifier[0] == identifier[-1] and identifier[0] in ("'", "\""):
            return identifier[1:-1]
        return ast.Undefined()

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
        res, ctx = a.analyze(MockPred(), {"l": True, "r": False})
        assert not res
        assert ctx.literals["l"] == True
        assert ctx.literals["r"] == False
        assert "Right hand side of AND operator at" in ctx.failed[0]

    def test_logical_eval2(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.LogicalOperator('and', l, r)
        res, ctx = a.analyze(MockPred(), {"l": True, "r": True})
        assert res
        assert ctx.literals["l"] == True
        assert ctx.literals["r"] == True

    def test_logical_eval3(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.LogicalOperator('or', l, r)
        res, ctx = a.analyze(MockPred(), {"l": False, "r": False})
        assert not res
        assert ctx.literals["l"] == False
        assert ctx.literals["r"] == False
        assert "Both sides of OR operator at" in ctx.failed[0]

    def test_logical_eval4(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.LogicalOperator('or', l, r)
        res, ctx = a.analyze(MockPred(), {"l": False, "r": True})
        assert res
        assert ctx.literals["l"] == False
        assert ctx.literals["r"] == True

    def test_logical_eval5(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.LogicalOperator('or', l, r)
        res, ctx = a.analyze(MockPred(), {"l": False})
        assert not res
        assert ctx.literals["l"] == False
        assert ctx.literals["r"] == ast.Undefined()
        assert "Both sides of OR operator" in ctx.failed[0]

    def test_logical_eval6(self):
        "Short circuit logic"
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.LogicalOperator('or', l, r)
        res, ctx = a.analyze(MockPred(), {"l": True})
        assert res
        assert ctx.literals["l"] == True
        assert "r" not in ctx.literals

    def test_logical_eval7(self):
        "Short circuit logic"
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.LogicalOperator('and', l, r)
        res, ctx = a.analyze(MockPred(), {"l": False})
        assert not res
        assert ctx.literals["l"] == False
        assert "r" not in ctx.literals
        assert "Left hand side" in ctx.failed[0]

    def test_negate_false(self):
        l = ast.Literal("l")
        a = ast.NegateOperator(l)
        res, ctx = a.analyze(MockPred(), {"l": False})
        assert res
        assert ctx.literals["l"] == False

    def test_negate_true(self):
        l = ast.Literal("l")
        a = ast.NegateOperator(l)
        res, ctx = a.analyze(MockPred(), {"l": True})
        assert not res
        assert ctx.literals["l"] == True

    @pytest.mark.parametrize(("type",), [
        (">=",), (">",), ("<",), ("<=",), ("=",), ("!=",), ("is",)])
    def test_compare(self, type):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.CompareOperator(type, l, r)
        d = {"l": 1, "r": 5}
        res, ctx = a.analyze(MockPred(), d)

        # Determine the expected result
        if type == "=":
            s = '%d %s %d' % (d["l"], "==", d["r"])
        else:
            s = '%d %s %d' % (d["l"], type, d["r"])
        expected = eval(s)

        assert res == expected
        if not res:
            assert ("%s comparison at" % type.upper()) in ctx.failed[0]
        assert ctx.literals["l"] == d["l"]
        assert ctx.literals["r"] == d["r"]

    @pytest.mark.parametrize(("type",), [
        (">=",), (">",), ("<",), ("<=",), ("=",), ("!=",), ("is",)])
    def test_compare_undef(self, type):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.CompareOperator(type, l, r)
        d = {"l": 1}
        res, ctx = a.analyze(MockPred(), d)

        # Determine the expected result
        if type == "!=":
            assert res
        else:
            assert not res
        if not res:
            assert ("%s comparison at" % type.upper()) in ctx.failed[0]
        assert ctx.literals["l"] == d["l"]
        assert ctx.literals["r"] == ast.Undefined()

    @pytest.mark.parametrize(("type",), [
        (">=",), (">",), ("<",), ("<=",), ("=",), ("!=",), ("is",)])
    def test_compare_empty(self, type):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.CompareOperator(type, l, r)
        d = {"l": 1, "r": ast.Empty()}
        res, ctx = a.analyze(MockPred(), d)

        # Determine the expected result
        if type == "!=":
            assert res
        else:
            assert not res
        if not res:
            assert ("%s comparison at" % type.upper()) in ctx.failed[0]
        assert ctx.literals["l"] == d["l"]
        assert ctx.literals["r"] == ast.Empty()

    def test_contains_invalid(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.ContainsOperator(l, r)
        d = {"l": 1, "r": None}
        res, ctx = a.analyze(MockPred(), d)
        assert not res
        assert "does not support contains" in ctx.failed[0]
        assert ctx.literals["l"] == 1
        assert "r" not in ctx.literals

    def test_contains_undef(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.ContainsOperator(l, r)
        d = {"r": 5}
        res, ctx = a.analyze(MockPred(), d)
        assert not res
        assert "not in left side" in ctx.failed[0]
        assert ctx.literals["l"] == ast.Undefined()
        assert ctx.literals["r"] == 5

    def test_contains_empty(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.ContainsOperator(l, r)
        d = {"l": [], "r": 5}
        res, ctx = a.analyze(MockPred(), d)
        assert not res
        assert "not in left side" in ctx.failed[0]
        assert ctx.literals["l"] == []
        assert ctx.literals["r"] == 5

    def test_contains_valid(self):
        l = ast.Literal("l")
        r = ast.Literal("r")
        a = ast.ContainsOperator(l, r)
        d = {"l": [42], "r": 42}
        res, ctx = a.analyze(MockPred(), d)
        assert res
        assert ctx.literals["l"] == [42]
        assert ctx.literals["r"] == 42

    def test_match_bad_types(self):
        l = ast.Literal("l")
        r = ast.Regex(ast.Literal('abcd'))
        a = ast.MatchOperator(l, r)
        d = {"l": 42}
        res, ctx = a.analyze(MockPred(), d)
        assert not res
        assert "not a string" in ctx.failed[0]
        assert ctx.literals["l"] == 42

    def test_match_undef(self):
        l = ast.Literal("l")
        r = ast.Regex(ast.Literal('abcd'))
        a = ast.MatchOperator(l, r)
        d = {}
        res, ctx = a.analyze(MockPred(), d)
        assert not res
        assert "not a string" in ctx.failed[0]
        assert ctx.literals["l"] == ast.Undefined()

    def test_match_no_match(self):
        l = ast.Literal("l")
        r = ast.Regex(ast.Literal('abcd'))
        a = ast.MatchOperator(l, r)
        d = {"l": "tubez"}
        res, ctx = a.analyze(MockPred(), d)
        assert not res
        assert "does not match" in ctx.failed[0]
        assert ctx.literals["l"] == "tubez"

    def test_match(self):
        l = ast.Literal("l")
        r = ast.Regex(ast.Literal('abcd'))
        a = ast.MatchOperator(l, r)
        d = {"l": "abcd"}
        res, ctx = a.analyze(MockPred(), d)
        assert res
        assert ctx.literals["l"] == "abcd"

    def test_push(self):
        p = ast.PushResult(True, ast.Constant(True))
        class TestSet(object):
            def __init__(self):
                self.res = []
            def push_match(self, m):
                self.res.append(m)

        testset = TestSet()
        assert p.evaluate(testset, {})
        assert testset.res == [True]

    def test_branch(self):
        l = ast.Literal('a')
        r = ast.Literal('b')
        check = ast.CompareOperator('>', l, r)
        true = ast.Constant(True)
        false = ast.Constant(False)
        b = ast.Branch(check, true, false)

        assert b.evaluate(MockPred(), {'a': 2, 'b':1})

        res, ctx = b.analyze(MockPred(), {'a': 1, 'b':2})
        assert not res
        assert ctx.literals["a"] == 1
        assert ctx.literals["b"] == 2
        assert ctx.failed[-1].startswith("Right hand side")

    def test_both_false(self):
        c1 = ast.Constant(False)
        c2 = ast.Constant(False)
        n = ast.Both(c1, c2)
        assert n.evaluate(MockPred(), {}) == False

    def test_iterall_true(self):
        c1 = ast.Constant(False)
        c2 = ast.Constant(True)
        n = ast.Both(c1, c2)
        assert n.evaluate(MockPred(), {}) == True

    def test_cached_node_uses_cache(self):
        c = ast.Constant(False)
        n = ast.CachedNode(c, 0)

        ctx = ast.EvalContext(MockPred(), {})
        ctx.cached_res[0] = True

        assert n.eval(ctx)

    def test_cached_node_sets_cache(self):
        c = ast.Constant(False)
        n = ast.CachedNode(c, 0)

        ctx = ast.EvalContext(MockPred(), {})

        assert not n.eval(ctx)
        assert not ctx.cached_res[0]

    def test_litset_eval(self):
        s = ast.LiteralSet([ast.Constant(True), ast.Literal('a'), ast.Literal('b')])
        ctx = ast.EvalContext(MockPred(), {'a': 2, 'b': False})
        res = s.eval(ctx)
        assert isinstance(res, frozenset)
        assert True in res
        assert False in res
        assert 2 in res

    def test_litset_static(self):
        s = ast.LiteralSet([ast.Constant(True), ast.Literal('\"a\"')])
        pred = MockPred()
        s.static_resolve(pred)
        ctx = ast.EvalContext(pred, {'a': 2, 'b': False})
        res = s.eval(ctx)
        assert s.static
        assert isinstance(res, set)
        assert True in res
        assert "a" in res

