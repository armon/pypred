from pypred import predicate, merge, ast

class TestMerge(object):
    def test_names(self):
        n1 = ast.Literal("foo")
        assert ("Literal", "foo") == merge.node_name(n1)
        n2 = ast.Number(12)
        assert ("Number", 12) == merge.node_name(n2)
        n3 = ast.Constant(True)
        assert ("Constant", True) == merge.node_name(n3)
        n4 = ast.Regex("^tubez$")
        assert ("Regex", "^tubez$") == merge.node_name(n4)
        n5 = ast.Undefined()
        assert "Undefined" == merge.node_name(n5)
        n6 = ast.Empty()
        assert "Empty" == merge.node_name(n6)

        # Negate does not emit the operator!
        n7 = ast.NegateOperator(n3)
        assert ("Constant", True) == merge.node_name(n7)

        n8 = ast.CompareOperator('=', n1, n2)
        n8_name = merge.node_name(n8)
        assert ("CompareOperator", "=", ("Literal", "foo"), ("Number", 12)) == n8_name
        n8_static = merge.node_name(n8, True)
        assert ("CompareOperator", "equality", ("Literal", "foo"), ("Number", "static")) == n8_static

        n9 = ast.MatchOperator(n1, n4)
        n9_name = merge.node_name(n9)
        assert ("MatchOperator", ("Literal", "foo"), ("Regex", "^tubez$")) == n9_name
        n10 = ast.ContainsOperator(n1, n2)
        n10_name = merge.node_name(n10)
        assert ("ContainsOperator", ("Literal", "foo"), ("Number", 12.0)) == n10_name

        # Logical operator returns literal!
        n11 = ast.LogicalOperator('and', n1, n3)
        n11_name = merge.node_name(n11)
        assert ("Literal", "foo") == n11_name

    def test_count(self):
        pred_str = """foo > 12 and bar != 0 or not test and
name matches '^test$' and list contains elem and foo > 20
"""
        p1 = predicate.Predicate(pred_str)
        count, names = merge.count_expressions(p1.ast)

        assert len(count) == 5
        assert ("Literal", "test") in names

        k = ("CompareOperator", "order", ("Literal", "foo"), ("Number", "static"))
        assert k in names
        assert count[k] == 2

