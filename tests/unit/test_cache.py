from pypred import ast, cache

class TestCache(object):

    def test_cache(self):
        l = ast.Literal('foo')
        v = ast.Number(42)
        gt1 = ast.CompareOperator('>', l, v)

        l1 = ast.Literal('foo')
        v1 = ast.Number(42)
        gt2 = ast.CompareOperator('>', l1, v1)
        n = ast.LogicalOperator('or', gt1, gt2)
        cache.cache_expressions(n)

        # Both sides should be dedupped
        assert n.left is n.right
        assert n.left.cache_id == 0

