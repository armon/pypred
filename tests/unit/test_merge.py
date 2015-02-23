from pypred import predicate, merge, ast

try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

DEEP = merge.RefactorSettings.deep()

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

        # Literal set just uses name
        n12 = ast.LiteralSet([n1, n2])
        n12_name = merge.node_name(n12)
        assert "LiteralSet" == n12_name

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

    def test_rewrite_norm(self):
        "Test a simple re-write"
        l = ast.Literal('foo')
        r = ast.Literal('bar')
        c = ast.LogicalOperator('or', l, r)
        name = merge.node_name(c)
        merge.rewrite_ast(c, name, l, True)
        assert isinstance(c.left, ast.Constant)

    def test_rewrite_compare(self):
        "Checks that a compare rewrite uses compare module"
        l = ast.Literal('foo')
        r = ast.Literal('bar')
        n = ast.CompareOperator('>', l, r)
        name = merge.node_name(n)
        with patch('pypred.merge.compare.compare_rewrite') as c:
            merge.rewrite_ast(n, name, n, True)
            assert c.called

    def test_rewrite_contains(self):
        "Checks that a contain rewrite uses contains module"
        l = ast.LiteralSet([ast.Number(1), ast.Number(2)])
        r = ast.Literal('bar')
        c = ast.ContainsOperator(l, r)
        name = merge.node_name(c)
        with patch('pypred.merge.contains.contains_rewrite') as cr:
            merge.rewrite_ast(c, name, c, True)
            assert cr.called

    def test_select_expr_negate(self):
        "Checks that a negate operation is not selected"
        l = ast.Literal('foo')
        n = ast.NegateOperator(l)
        name = merge.node_name(n)
        expr = merge.select_rewrite_expression(DEEP, name, [n])
        assert expr == l

    def test_select_expr_logical(self):
        "Checks that a logical operation is not selected"
        l = ast.Literal('foo')
        r = ast.Literal('bar')
        n = ast.LogicalOperator('or', l, r)
        name = merge.node_name(n)
        expr = merge.select_rewrite_expression(DEEP, name, [n])
        assert expr == l
        n.left = None
        expr = merge.select_rewrite_expression(DEEP, name, [n])
        assert expr == r

    def test_select_expr_first(self):
        "Checks that first expression is selected"
        l = ast.Literal('foo')
        r = ast.Literal('bar')
        name = merge.node_name(l)
        expr = merge.select_rewrite_expression(DEEP, name, [l, r])
        assert expr == l

    def test_select_expr_compare(self):
        "Checks that a compare operation uses compare module"
        l = ast.Literal('foo')
        r = ast.Literal('bar')
        n = ast.CompareOperator('>', l, r)
        name = merge.node_name(n)

        with patch('pypred.merge.compare.select_rewrite_expression') as c:
            merge.select_rewrite_expression(DEEP, name, [n])
            assert c.called

    def test_select_expr_contains(self):
        "Checks that a contains operation uses contains module"
        l = ast.LiteralSet([ast.Number(1), ast.Number(2)])
        r = ast.Literal('bar')
        c = ast.ContainsOperator(l, r)
        name = merge.node_name(c)

        with patch('pypred.merge.contains.select_rewrite_expression') as cr:
            merge.select_rewrite_expression(DEEP, name, [c])
            assert cr.called

    def test_merge(self):
        "Tests a simple merge"
        p1 = predicate.Predicate('foo')
        p2 = predicate.Predicate('bar')
        p3 = predicate.Predicate('baz')
        p4 = predicate.Predicate('zip')
        m = merge.merge([p1,p2,p3,p4])
        assert isinstance(m, ast.Both)
        assert isinstance(m.left, ast.Both)
        assert isinstance(m.right, ast.Both)
        assert m.left.left.pred    == p1
        assert m.left.right.pred   == p2
        assert m.right.left.pred   == p3
        assert m.right.right.pred  == p4



