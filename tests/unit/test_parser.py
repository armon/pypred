"""
Unit tests for the lexer
"""
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
        assert len(names) == len(exp_nodes)
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


