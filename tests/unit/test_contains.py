from pypred import ast, contains, merge

class TestContains(object):
    def test_select_rewrite(self):
        "Test rewrite selection"
        s1 = ast.LiteralSet([ast.Number(1), ast.Number(2), ast.Number(3)])
        s2 = ast.LiteralSet([ast.Number(1)])
        s3 = ast.LiteralSet([ast.Number(1), ast.Number(2), ast.Number(3), ast.Number(4), ast.Number(5)])
        l = ast.Literal('foo')
        c1 = ast.ContainsOperator(s1, l)
        c2 = ast.ContainsOperator(s2, l)
        c3 = ast.ContainsOperator(s3, l)

        name = merge.node_name(c1, True)
        select = contains.select_rewrite_expression(name, [c1, c2, c3])
        assert select is c1

    def test_contains_rewrite(self):
        s1 = ast.LiteralSet([ast.Number(1), ast.Number(2), ast.Number(3)])
        s2 = ast.LiteralSet([ast.Number(1)])
        s3 = ast.LiteralSet([ast.Number(1), ast.Number(2), ast.Number(3), ast.Number(4), ast.Number(5)])
        s4 = ast.LiteralSet([ast.Number(6)])
        l = ast.Literal('foo')
        c1 = ast.ContainsOperator(s1, l)
        c2 = ast.ContainsOperator(s2, l)
        c3 = ast.ContainsOperator(s3, l)
        c4 = ast.ContainsOperator(s4, l)

        # Rewrite set1 as True, s3 is super set, should be True
        name = merge.node_name(c1, True)
        r = contains.contains_rewrite(c3, name, c1, True)
        assert isinstance(r, ast.Constant) and r.value == True

        # Rewrite set1 as False, s3 is super set, should be trimed
        name = merge.node_name(c1, True)
        r = contains.contains_rewrite(c3, name, c1, False)
        assert len(r.left.value) == 2
        assert ast.Number(4) in r.left.value
        assert ast.Number(5) in r.left.value

        # Rewrite set1 as True, s2 is sub set, should check value
        r = contains.contains_rewrite(c2, name, c1, True)
        assert len(r.left.value) == 1

        # Rewrite set1 as False, s2 is subset, should be false
        r = contains.contains_rewrite(c2, name, c1, False)
        assert isinstance(r, ast.Constant) and r.value == False

        # Rewrite set1 as True, s4 has no overlap, should be false
        r = contains.contains_rewrite(c4, name, c1, True)
        assert isinstance(r, ast.Constant) and r.value == False

        # Rewrite set1 as False, s4 is no overlap, should check
        r = contains.contains_rewrite(c4, name, c1, False)
        assert len(r.left.value) == 1
        assert ast.Number(6) in r.left.value

