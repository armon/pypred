"""
Unit tests for the lexer
"""
import pytest
from pypred import parser, ast

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

