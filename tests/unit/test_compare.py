from pypred import ast, compare, merge
from pypred.tiler import ASTPattern

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

    def test_equality_rewrite_static(self):
        "Test an equality rewrite with static values"
        l = ast.Literal('foo')
        s = ast.Literal('"test"')
        s.static = True
        s.static_val = "test"
        cmp1 = ast.CompareOperator('=', l, s)
        cmp2 = ast.CompareOperator('!=', l, s)
        or1 = ast.LogicalOperator('or', cmp1, cmp2)

        # Rewrite foo = "test" as True
        # Left should be True, right should be False
        name = merge.node_name(cmp1, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp1, True)

        assert isinstance(r.left, ast.Constant)
        assert r.left.value == True
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == False

        # Rewrite foo = "test" as False
        # Left should be False, right should be True
        name = merge.node_name(cmp1, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp1, False)

        assert isinstance(r.left, ast.Constant)
        assert r.left.value == False
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == True

        # Rewrite foo != "test" as True
        # Left should be False, right should be True
        name = merge.node_name(cmp2, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp2, True)

        assert isinstance(r.left, ast.Constant)
        assert r.left.value == False
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == True

        # Rewrite foo != "test" as False
        # Left should be False, right should be True
        name = merge.node_name(cmp2, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp2, False)

        assert isinstance(r.left, ast.Constant)
        assert r.left.value == True
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == False

    def test_equality_rewrite_diff_static(self):
        "Test an equality rewrite with different static values"
        l = ast.Literal('foo')
        s = ast.Literal('"test"')
        s.static = True
        s.static_val = "test"

        s1 = ast.Literal('"other"')
        s1.static = True
        s1.static_val = "other"

        cmp1 = ast.CompareOperator('=', l, s)
        cmp2 = ast.CompareOperator('=', l, s1)
        or1 = ast.LogicalOperator('or', cmp1, cmp2)

        # Rewrite foo = "test" as True
        # Left should be True, right should be False
        name = merge.node_name(cmp1, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp1, True)

        assert isinstance(r.left, ast.Constant)
        assert r.left.value == True
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == False

        # Rewrite foo = "test" as False
        # Left should be False, right should be same
        name = merge.node_name(cmp1, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp1, False)

        assert isinstance(r.left, ast.Constant)
        assert r.left.value == False
        assert ASTPattern(cmp2).matches(r.right)

        # Rewrite foo = "other" as True
        # Left should be False, right should be True
        name = merge.node_name(cmp2, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp2, True)

        assert isinstance(r.left, ast.Constant)
        assert r.left.value == False
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == True

        # Rewrite foo = "other" as False
        # Left should be same, right should be False
        name = merge.node_name(cmp2, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp2, False)

        assert ASTPattern(cmp1).matches(r.left)
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == False

    def test_equality_rewrite_non_static(self):
        "Test an equality rewrite with non-static values"
        l = ast.Literal('foo')
        v = ast.Literal('bar')
        cmp1 = ast.CompareOperator('=', l, v)
        cmp2 = ast.CompareOperator('!=', l, v)
        or1 = ast.LogicalOperator('or', cmp1, cmp2)

        # Rewrite foo = bar as True
        # Left should be True, right should be False
        name = merge.node_name(cmp1, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp1, True)

        assert isinstance(r.left, ast.Constant)
        assert r.left.value == True
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == False

        # Rewrite foo = bar as False
        # Left should be False, right should be True
        name = merge.node_name(cmp1, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp1, False)

        assert isinstance(r.left, ast.Constant)
        assert r.left.value == False
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == True

        # Rewrite foo != bar as True
        # Left should be False, right should be True
        name = merge.node_name(cmp2, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp2, True)

        assert isinstance(r.left, ast.Constant)
        assert r.left.value == False
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == True

        # Rewrite foo != bar as False
        # Left should be False, right should be True
        name = merge.node_name(cmp2, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp2, False)

        assert isinstance(r.left, ast.Constant)
        assert r.left.value == True
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == False

    def test_equality_rewrite_literals(self):
        "Test an equality rewrite with different literals"
        l = ast.Literal('foo')
        v = ast.Literal('bar')
        v2 = ast.Literal('baz')
        cmp1 = ast.CompareOperator('=', l, v)
        cmp2 = ast.CompareOperator('=', l, v2)
        or1 = ast.LogicalOperator('or', cmp1, cmp2)

        # Rewrite foo = bar as True
        # Left should be True, right should be unchanged
        name = merge.node_name(cmp1, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp1, True)

        assert isinstance(r.left, ast.Constant)
        assert r.left.value == True
        assert ASTPattern(cmp2).matches(r.right)

        # Rewrite foo = bar as False
        # Left should be False, right should be same
        name = merge.node_name(cmp1, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp1, False)

        assert isinstance(r.left, ast.Constant)
        assert r.left.value == False
        assert ASTPattern(cmp2).matches(r.right)

        # Rewrite foo = baz as True
        # Left should be same, right should be True
        name = merge.node_name(cmp2, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp2, True)

        assert ASTPattern(cmp1).matches(r.left)
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == True

        # Rewrite foo = baz as False
        # Left should be same, right should be False
        name = merge.node_name(cmp2, True)
        r = compare.equality_rewrite(ast.dup(or1), name, cmp2, False)

        assert ASTPattern(cmp1).matches(r.left)
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == False

