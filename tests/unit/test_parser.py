"""
Unit tests for the lexer
"""
import pytest
from pypred import parser, ast

class TestParser(object):
    def assert_nodes(self, inp, exp_nodes):
        lexer = parser.get_lexer()
        p = parser.get_parser()
        res = p.parse(inp, lexer=lexer)
        assert isinstance(res, ast.Node)

        # Do a pre-order traversal
        nodes = []
        res.pre(lambda n: nodes.append(n))

        # Get the class names
        names = [repr(n) for n in nodes]
        #assert len(names) == len(exp_nodes)
        assert names == exp_nodes

    def test_jack_and_jill(self):
        inp = "name is Jack and friend_name is Jill"
        self.assert_nodes(inp, [
            "LogicalOperator t:and l:CompareOperator r:CompareOperator",
            "CompareOperator t:is l:Literal r:Literal",
            "Literal v:name",
            "Literal v:Jack",
            "CompareOperator t:is l:Literal r:Literal",
            "Literal v:friend_name",
            "Literal v:Jill"
        ])

    def test_event_parse(self):
        inp = 'event is "Record Score" and \
        ((score >= 500 and highest_score_wins) or (score < 10 and lowest_score_wins))'
        self.assert_nodes(inp, [
"LogicalOperator t:and l:CompareOperator r:LogicalOperator",
    "CompareOperator t:is l:Literal r:Literal",
        "Literal v:event",
        "Literal v:\"Record Score\"",
    "LogicalOperator t:or l:LogicalOperator r:LogicalOperator",
        "LogicalOperator t:and l:CompareOperator r:Literal",
            "CompareOperator t:>= l:Literal r:Number",
                "Literal v:score",
                "Number v:500.0",
            "Literal v:highest_score_wins",
        "LogicalOperator t:and l:CompareOperator r:Literal",
            "CompareOperator t:< l:Literal r:Number",
                "Literal v:score",
                "Number v:10.0",
            "Literal v:lowest_score_wins",
        ])

    def test_server_parse(self):
        inp ='server matches "east-web-([\d]+)" and errors contains "CPU load" and environment != test'
        self.assert_nodes(inp, [
"LogicalOperator t:and l:MatchOperator r:LogicalOperator",
    "MatchOperator l:Literal r:Regex",
        "Literal v:server",
        "Regex v:east-web-([\d]+)",
     "LogicalOperator t:and l:ContainsOperator r:CompareOperator",
        "ContainsOperator l:Literal r:Literal",
            "Literal v:errors",
            "Literal v:\"CPU load\"",
        "CompareOperator t:!= l:Literal r:Literal",
            "Literal v:environment",
            "Literal v:test"
        ])

    def test_logical_precedence(self):
        inp = "true or false and false"
        self.assert_nodes(inp, [
"LogicalOperator t:or l:Constant r:LogicalOperator",
    "Constant v:True",
    "LogicalOperator t:and l:Constant r:Constant",
        "Constant v:False",
        "Constant v:False",
])

    def test_logical_precedence_2(self):
        inp = "true and false or false"
        self.assert_nodes(inp, [
"LogicalOperator t:and l:Constant r:LogicalOperator",
    "Constant v:True",
    "LogicalOperator t:or l:Constant r:Constant",
        "Constant v:False",
        "Constant v:False",
])
    def test_logical_not_precedence(self):
        inp = "false or not true"
        self.assert_nodes(inp, [
"LogicalOperator t:or l:Constant r:NegateOperator",
    "Constant v:False",
    "NegateOperator l:Constant",
        "Constant v:True",
])

    def test_undef_and_empty(self):
        inp = "errors is undefined or errors is empty"
        self.assert_nodes(inp, [
"LogicalOperator t:or l:CompareOperator r:CompareOperator",
    "CompareOperator t:is l:Literal r:Undefined",
        "Literal v:errors",
        "Undefined",
    "CompareOperator t:is l:Literal r:Empty",
        "Literal v:errors",
        "Empty"
])

    def test_null(self):
        inp = "bad is null"
        self.assert_nodes(inp, [
"CompareOperator t:is l:Literal r:Constant",
    "Literal v:bad",
    "Constant v:None"
])

    def test_is_not(self):
        inp = "bad is not null"
        self.assert_nodes(inp, [
"CompareOperator t:!= l:Literal r:Constant",
    "Literal v:bad",
    "Constant v:None"
])

    def test_literal_set(self):
        inp = "{true false 1.0 \"quote\"}"
        lexer = parser.get_lexer()
        p = parser.get_parser()
        res = p.parse(inp, lexer=lexer)
        assert isinstance(res, ast.LiteralSet)
        assert res.value == set([
            ast.Constant(True),
            ast.Constant(False),
            ast.Number(1.0),
            ast.Literal("\"quote\"")
        ])

    def test_literal_set_empty(self):
        inp = "{}"
        lexer = parser.get_lexer()
        p = parser.get_parser()
        res = p.parse(inp, lexer=lexer)
        assert isinstance(res, ast.LiteralSet)
        assert res.value == set([])

    def test_error_end(self):
        inp = "false and"
        lexer = parser.get_lexer()
        p = parser.get_parser()
        with pytest.raises(SyntaxError):
            p.parse(inp, lexer=lexer)

    def test_error_expr(self):
        inp = "a > 1 b > 2"
        lexer = parser.get_lexer()
        p = parser.get_parser()
        lexer.parser = p
        res = p.parse(inp, lexer=lexer)
        assert isinstance(res, ast.CompareOperator)
        assert len(p.errors) == 3

