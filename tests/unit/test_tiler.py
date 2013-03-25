from pypred import ast, tiler

class TestTiler(object):
    def test_pattern_match(self):
        p = tiler.Pattern()
        assert p.matches(None)

    def test_ast_pattern(self):
        l = ast.Literal('foo')
        b = ast.Literal('bar')
        c = ast.CompareOperator('is', l, b)
        p = tiler.ASTPattern(c)
        assert p.matches(c)

        # Change a node
        z = ast.Number(42)
        c1 = ast.CompareOperator('is', l, z)
        assert not p.matches(c1)

    def test_simple_sub_pattern(self):
        l = ast.Literal('foo')
        r = ast.Regex('^tubez$')
        n = ast.MatchOperator(l, r)
        p = tiler.SimplePattern('types:MatchOperator',
                tiler.ASTPattern(l), 'types:Regex')
        assert p.matches(n)

    def test_simple_pattern_type(self):
        l = ast.Literal('foo')
        r = ast.Regex('^tubez$')
        n = ast.MatchOperator(l, r)
        p = tiler.SimplePattern('types:MatchOperator',
                'types:Literal', 'types:Regex')
        assert p.matches(n)

    def test_simple_pattern_value(self):
        l = ast.Literal('foo')
        r = ast.Constant(True)
        n = ast.CompareOperator('=', l, r)
        p = tiler.SimplePattern('types:CompareOperator AND ops:=',
                'types:Literal', 'types:Constant AND value:True')
        assert p.matches(n)

    def test_simple_pattern_op(self):
        l = ast.Literal('foo')
        r = ast.Literal('foo')
        n = ast.CompareOperator('=', l, r)
        p = tiler.SimplePattern('op:=',
                'types:Literal', 'types:Literal')
        assert p.matches(n)

    def test_simple_pattern_ops(self):
        l = ast.Literal('foo')
        r = ast.Literal('foo')
        n = ast.CompareOperator('<=', l, r)
        p = tiler.SimplePattern('ops:>,>=,<,<=',
                'types:Literal', 'types:Literal')
        assert p.matches(n)

    def test_simple_pattern_op_type(self):
        l = ast.Literal('foo')
        r = ast.Literal('foo')
        n = ast.CompareOperator('>', l, r)
        p = tiler.SimplePattern('types:CompareOperator AND op:=',
                'types:Literal', 'types:Literal')
        assert not p.matches(n)

        n = ast.CompareOperator('=', l, r)
        assert p.matches(n)

    def test_tile(self):
        p = tiler.SimplePattern('types:CompareOperator AND op:=',
                'types:Literal', 'types:Literal')

        l1 = ast.Literal('foo')
        r1 = ast.Literal('bar')
        n1 = ast.CompareOperator('=', l1, r1)

        l2 = ast.Literal('zip')
        r2 = ast.Literal('baz')
        n2 = ast.CompareOperator('=', l2, r2)

        n = ast.LogicalOperator('or', n1, n2)

        i = {'count': 0}
        def func(pattern, node):
            assert pattern == p
            count = i['count']
            if count == 0:
                assert node == n1
            if count == 1:
                assert node == n2
            i['count'] += 1

        assert n == tiler.tile(n, [p], func)
        assert i['count'] == 2

