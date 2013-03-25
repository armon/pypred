from pypred import ast, compact

class TestCompact(object):

    def test_compact(self):
        l = ast.Literal('foo')
        v = ast.Number(42)
        gt = ast.CompareOperator('>', l, v)

        l1 = ast.Literal('foo')
        v1 = ast.Number(42)
        lt = ast.CompareOperator('<', l1, v1)
        n = ast.LogicalOperator('or', gt, lt)
        compact.compact(n)

        # Literal and number should be de-dupped
        assert l is n.right.left
        assert v is n.right.right

    def test_names(self):
        n1 = ast.Literal("foo")
        assert ("Literal", "foo") == compact.node_name(n1)

        n2 = ast.Number(12)
        assert ("Number", 12) == compact.node_name(n2)

        n3 = ast.Constant(True)
        assert ("Constant", True) == compact.node_name(n3)

        n4 = ast.Regex("^tubez$")
        assert ("Regex", "^tubez$") == compact.node_name(n4)

        n5 = ast.Undefined()
        assert "Undefined" == compact.node_name(n5)

        n6 = ast.Empty()
        assert "Empty" == compact.node_name(n6)

        n7 = ast.NegateOperator(n3)
        assert ("NegateOperator", ("Constant", True)) == compact.node_name(n7)

        n8 = ast.CompareOperator('=', n1, n2)
        n8_name = compact.node_name(n8)
        assert ("CompareOperator", "=", ("Literal", "foo"), ("Number", 12)) == n8_name

        n9 = ast.MatchOperator(n1, n4)
        n9_name = compact.node_name(n9)
        assert ("MatchOperator", ("Literal", "foo"), ("Regex", "^tubez$")) == n9_name

        n10 = ast.ContainsOperator(n1, n2)
        n10_name = compact.node_name(n10)
        assert ("ContainsOperator", ("Literal", "foo"), ("Number", 12.0)) == n10_name

        n11 = ast.LogicalOperator('and', n1, n3)
        n11_name = compact.node_name(n11)
        assert ("LogicalOperator", "and", ("Literal", "foo"), ("Constant", True)) == n11_name

