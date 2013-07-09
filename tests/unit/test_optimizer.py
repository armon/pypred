from pypred import optimizer, ast

class TestOptimizer(object):
    def test_no_pass(self):
        "Should do nothing"
        assert None == optimizer.optimize(None, max_pass=0, min_change=1)

    def test_min_change(self):
        t = ast.Constant(True)
        f = ast.Constant(False)
        left = ast.LogicalOperator('or', t, f)
        right = ast.LogicalOperator('and', t, f)
        r = ast.LogicalOperator('or', left, right)

        # First pass will only replace the left and right
        # with constants, but will not cause 3 changes.
        r = optimizer.optimize(r, max_pass=10, min_change=3)

        assert isinstance(r, ast.LogicalOperator)
        assert isinstance(r.left, ast.Constant)
        assert r.left.value == True
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == False

    def test_max_pass(self):
        t = ast.Constant(True)
        f = ast.Constant(False)
        left = ast.LogicalOperator('or', t, f)
        right = ast.LogicalOperator('and', t, f)
        r = ast.LogicalOperator('or', left, right)

        # First pass will only replace the left and right
        # with constants, but will not cause replace root
        r = optimizer.optimize(r, max_pass=1, min_change=1)

        assert isinstance(r, ast.LogicalOperator)
        assert isinstance(r.left, ast.Constant)
        assert r.left.value == True
        assert isinstance(r.right, ast.Constant)
        assert r.right.value == False

    def test_and_replace(self):
        "Test AND -> False"
        t = ast.Constant(True)
        f = ast.Constant(False)
        n = ast.LogicalOperator('and', t, f)

        # Should reduce to False
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert isinstance(r, ast.Constant)
        assert r.value == False

        # Should reduce to False
        n = ast.LogicalOperator('and', f, t)
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert isinstance(r, ast.Constant)
        assert r.value == False

    def test_or_replace(self):
        "Test OR -> True"
        t = ast.Constant(True)
        f = ast.Constant(False)
        n = ast.LogicalOperator('or', t, f)

        # Should reduce to True
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert isinstance(r, ast.Constant)
        assert r.value == True

        # Should reduce to True
        n = ast.LogicalOperator('or', f, t)
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert isinstance(r, ast.Constant)
        assert r.value == True

    def test_negate(self):
        "Test negation static analysis"
        t = ast.Constant(True)
        f = ast.Constant(False)
        n = ast.NegateOperator(t)

        # Should reduce to False
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert isinstance(r, ast.Constant)
        assert r.value == False

        # Should reduce to True
        n = ast.NegateOperator(f)
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert isinstance(r, ast.Constant)
        assert r.value == True

    def test_push_result(self):
        "Test false push result"
        f = ast.Constant(False)
        n = ast.PushResult(None, f)

        # Should reduce to False
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert isinstance(r, ast.Constant)
        assert r.value == False

    def test_both_all_false(self):
        "Test removing a both node when both sides are false"
        f = ast.Constant(False)
        n = ast.Both(f, f)

        # Should reduce to False
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert isinstance(r, ast.Constant)
        assert r.value == False

    def test_both_dead(self):
        "Test removing a both node when one side is dead"
        t = ast.Constant(True)
        f = ast.Constant(False)

        # Should reduce to left
        n = ast.Both(t, f)
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert r is t

        # Should reduce to right
        n = ast.Both(f, t)
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert r is t

    def test_or_dead(self):
        "Tests removing OR with dead branch"
        f = ast.Constant(False)
        l = ast.Literal('foo')
        v = ast.Number(42)
        cmp = ast.CompareOperator('=', l, v)
        n = ast.LogicalOperator('or', f, cmp)

        # Should reduce to to the compare
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert r is cmp

    def test_or_dead_right(self):
        "Tests removing OR with dead branch, right side"
        f = ast.Constant(False)
        l = ast.Literal('foo')
        v = ast.Number(42)
        cmp = ast.CompareOperator('=', l, v)
        n = ast.LogicalOperator('or', cmp, f)

        # Should reduce to to the compare
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert r is cmp

    def test_and_dead(self):
        "Tests removing AND with dead branch"
        t = ast.Constant(True)
        l = ast.Literal('foo')
        v = ast.Number(42)
        cmp = ast.CompareOperator('=', l, v)
        n = ast.LogicalOperator('and', t, cmp)

        # Should reduce to to the compare
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert r is cmp

    def test_and_dead_right(self):
        "Tests removing AND with dead branch, right side"
        t = ast.Constant(True)
        l = ast.Literal('foo')
        v = ast.Number(42)
        cmp = ast.CompareOperator('=', l, v)
        n = ast.LogicalOperator('and', cmp, t)

        # Should reduce to to the compare
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert r is cmp

    def test_branch_false_dead(self):
        "Test branch with the false branch being dead"
        t = ast.Constant(True)
        f = ast.Constant(False)
        l = ast.Literal('foo')
        v = ast.Number(42)
        cmp = ast.CompareOperator('=', l, v)
        n = ast.Branch(t, cmp, f)

        # Should reduce to to the compare
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert r is cmp

    def test_branch_true_dead(self):
        "Test branch with the false branch being dead"
        t = ast.Constant(True)
        f = ast.Constant(False)
        l = ast.Literal('foo')
        v = ast.Number(42)
        cmp = ast.CompareOperator('=', l, v)
        n = ast.Branch(f, t, cmp)

        # Should reduce to to the compare
        c, r = optimizer.optimization_pass(n)
        assert c == 1
        assert r is cmp

    def test_empty_set(self):
        "Test removing an empty literal set"
        s = ast.LiteralSet([])
        c, r = optimizer.optimization_pass(s)
        assert c == 1
        assert isinstance(r, ast.Empty)

    def test_empty_contains(self):
        "Tests removing an Empty contains X"
        e = ast.Empty()
        v = ast.Literal('foo')
        cn = ast.ContainsOperator(e, v)
        c, r = optimizer.optimization_pass(cn)
        assert c == 1
        assert isinstance(r, ast.Constant)
        assert r.value == False

    def test_undef_contains(self):
        "Tests removing an Empty contains X"
        u = ast.Undefined()
        v = ast.Literal('foo')
        cn = ast.ContainsOperator(u, v)
        c, r = optimizer.optimization_pass(cn)
        assert c == 1
        assert isinstance(r, ast.Constant)
        assert r.value == False

