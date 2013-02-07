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

