"""
Unit tests for the lexer
"""
from pypred import parser

class TestLexer(object):
    def assert_types(self, inp, expected):
        lexer = parser.get_lexer()
        lexer.input(inp)
        tokens = list(lexer)
        token_types = [t.type for t in tokens]
        assert len(token_types) == len(expected)
        for idx, (real, expect) in enumerate(zip(token_types, expected)):
            assert real == expect

    def test_jack_and_jill(self):
        inp = "name is Jack and friend_name is Jill"
        self.assert_types(inp, ['STRING', 'IS_EQUALS', 'STRING', 'AND', 'STRING', 'IS_EQUALS', 'STRING'])

    def test_event_parse(self):
        inp = 'event is "Record Score" and ((score >= 500 and highest_score_wins) or (score < 10 and lowest_score_wins))'
        expected = ['STRING', 'IS_EQUALS', 'STRING', 'AND', 'LPAREN', 'LPAREN', 'STRING', 'GREATER_THAN_EQUALS', 'NUMBER',
                'AND', 'STRING', 'RPAREN', 'OR', 'LPAREN', 'STRING', 'LESS_THAN', 'NUMBER', 'AND', 'STRING', 'RPAREN', 'RPAREN']
        self.assert_types(inp, expected)

    def test_server_parse(self):
        inp ='server matches "east-web-([\d]+)" and errors contains "CPU load" and environment != test'
        expected = ['STRING', 'MATCHES', 'STRING', 'AND', 'STRING', 'CONTAINS', 'STRING', 'AND', 'STRING',
                'NOT_EQUALS', 'STRING']
        self.assert_types(inp, expected)

    def test_logical_ops(self):
        inp = 'not valid and country is US or country is CA'
        expected = ['NOT', 'STRING', 'AND', 'STRING', 'IS_EQUALS', 'STRING', 'OR', 'STRING', 'IS_EQUALS', 'STRING']
        self.assert_types(inp, expected)

    def test_compare_ops(self):
        inp = "foo > 1 and bar >= 2 and baz < 3 and zip <= 4 and \n" + \
        "zap != true and zoo = undefined and zil is 5 and zek is not false"

        expected = ['STRING', 'GREATER_THAN', 'NUMBER', 'AND', 'STRING', 'GREATER_THAN_EQUALS',
                'NUMBER', 'AND', 'STRING', 'LESS_THAN', 'NUMBER', 'AND', 'STRING', 'LESS_THAN_EQUALS',
                'NUMBER', 'AND', 'STRING', 'NOT_EQUALS', 'TRUE', 'AND', 'STRING', 'EQUALS', 'UNDEFINED',
                'AND', 'STRING', 'IS_EQUALS', 'NUMBER', 'AND', 'STRING', 'IS_EQUALS', 'NOT', 'FALSE']
        self.assert_types(inp, expected)

    def test_parents(self):
        inp = "(((foo is bar)))"
        expected = ['LPAREN', 'LPAREN', 'LPAREN', 'STRING', 'IS_EQUALS', 'STRING', 'RPAREN', 'RPAREN', 'RPAREN']
        self.assert_types(inp, expected)

    def test_contains(self):
        inp = "errors contains 'BAD REQUEST'"
        expected = ['STRING', 'CONTAINS', 'STRING']
        self.assert_types(inp, expected)

    def test_matches(self):
        inp = "status matches 'ERROR.*'"
        expected = ['STRING', 'MATCHES', 'STRING']
        self.assert_types(inp, expected)

    def test_string_literals(self):
        inp = "plain string 'Longer with \"inner quote\"' \"reverse 'quote' \""
        expected = ['STRING', 'STRING', 'STRING', 'STRING']
        self.assert_types(inp, expected)

    def test_num_literals(self):
        inp = "5 5.0 -5.0 -1234 -0.123"
        expected = ['NUMBER', 'NUMBER', 'NUMBER', 'NUMBER', 'NUMBER']
        self.assert_types(inp, expected)

    def test_constants(self):
        inp = "true false undefined null empty"
        expected = ['TRUE', 'FALSE', 'UNDEFINED', 'NULL', 'EMPTY']
        self.assert_types(inp, expected)

    def test_error(self):
        inp = "!! foo"
        lexer = parser.get_lexer()
        lexer.input(inp)
        tokens = list(lexer)
        assert [t.type for t in tokens] == ['STRING']
        assert len(lexer.errors) == 1
        assert lexer.errors[0] == ('!!', 0, 1)

    def test_comments(self):
        inp = "# foo is bar\nfoo and bar"
        lexer = parser.get_lexer()
        lexer.input(inp)
        tokens = list(lexer)
        assert [t.type for t in tokens] == ['STRING', 'AND', 'STRING']

    def test_set_literal(self):
        inp = "{true false 1.0 \"quote\"}"
        expected = ['LBRACK', 'TRUE', 'FALSE', 'NUMBER', 'STRING', 'RBRACK']
        self.assert_types(inp, expected)

