from pypred import ast, tiler

class TestTiler(object):
    def test_simple_pattern_type(self):
        l = ast.Literal('foo')
        r = ast.Regex('^tubez$')
        n = ast.MatchOperator(l, r)
        p = tiler.SimplePattern('types:MatchOperator',
                'types:Literal', 'types:Regex')
        assert p.matches(n)

    def test_simple_pattern_op(self):
        l = ast.Literal('foo')
        r = ast.Literal('foo')
        n = ast.CompareOperator('=', l, r)
        p = tiler.SimplePattern('op:=',
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

