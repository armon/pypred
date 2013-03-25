from pypred import ast, compare, merge

class TestCompare(object):
    def test_canonical_non_literal(self):
        "Test canonicalization, literals on left"
        v = ast.Number(42)
        l = ast.Literal('foo')
        cmp = ast.CompareOperator('=', v, l)
        compare.canonicalize(cmp)

        assert cmp.left is l
        assert cmp.right is v

    def test_canonical_non_static(self):
        "Test canonicalization, literals on left"
        static = ast.Literal("'string'")
        static.static = True
        static.static_val = 'string'

        l = ast.Literal('foo')
        cmp = ast.CompareOperator('=', static, l)
        compare.canonicalize(cmp)

        assert cmp.left is l
        assert cmp.right is static

    def test_canonical_literal_order(self):
        "Test canonicalization, literals on left"
        l = ast.Literal('foo')
        r = ast.Literal('zip')
        cmp = ast.CompareOperator('>', r, l)
        compare.canonicalize(cmp)

        assert cmp.left is l
        assert cmp.right is r
        assert cmp.type == "<"

    def test_canonical_static_order(self):
        "Test canonicalization, static ordering"
        static = ast.Literal("'string'")
        static.static = True
        static.static_val = 'string'


        static2 = ast.Literal("'foo'")
        static2.static = True
        static2.static_val = 'foo'

        cmp = ast.CompareOperator('<', static, static2)
        compare.canonicalize(cmp)

        assert cmp.left is static2
        assert cmp.right is static
        assert cmp.type == ">"

    def test_select_rewrite_eq(self):
        "Test rewrite selection for equality"
        l = ast.Literal('foo')
        v = ast.Number(42)
        v2 = ast.Number(11)
        cmp1 = ast.CompareOperator('=', l, v2)
        cmp2 = ast.CompareOperator('=', l, v)
        cmp3 = ast.CompareOperator('=', l, v)

        name = merge.node_name(cmp1, True)
        select = compare.select_rewrite_expression(name, [cmp1,cmp2,cmp3])
        assert select is cmp2

    def test_select_rewrite_ord_numeric(self):
        "Test rewrite selection for ordered with numerics"
        l = ast.Literal('foo')
        v = ast.Number(42)
        v2 = ast.Number(11)
        v3 = ast.Number(100)
        cmp1 = ast.CompareOperator('>', l, v)
        cmp2 = ast.CompareOperator('<', l, v2)
        cmp3 = ast.CompareOperator('>', l, v3)

        name = merge.node_name(cmp1, True)
        select = compare.select_rewrite_expression(name, [cmp1,cmp2,cmp3])
        assert select is cmp1

    def test_select_rewrite_ord_literals(self):
        "Test rewrite selection for ordered with literals"
        l = ast.Literal('foo')
        v = ast.Literal('bar')
        v2 = ast.Literal('baz')
        cmp1 = ast.CompareOperator('>', l, v2)
        cmp2 = ast.CompareOperator('<', l, v)
        cmp3 = ast.CompareOperator('>', l, v)

        name = merge.node_name(cmp1, True)
        select = compare.select_rewrite_expression(name, [cmp1,cmp2,cmp3])
        assert select is cmp2


