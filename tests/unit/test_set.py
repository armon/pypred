import pytest
from pypred import OptimizedPredicateSet, PredicateSet, Predicate

class TestPredicateSet(object):
    def test_two(self):
        p1 = Predicate("name is 'Jack'")
        p2 = Predicate("name is 'Jill'")
        s = PredicateSet([p1, p2])
        match = s.evaluate({'name': 'Jill'})
        assert match == [p2]

    def test_dup(self):
        p1 = Predicate("name is 'Jill'")
        s = PredicateSet([p1, p1])
        match = s.evaluate({'name': 'Jill'})
        assert match == [p1]

class TestOptPredicateSet(object):
    def test_two(self):
        p1 = Predicate("name is 'Jack'")
        p2 = Predicate("name is 'Jill'")
        s = OptimizedPredicateSet([p1, p2])
        match = s.evaluate({'name': 'Jill'})
        assert match == [p2]

    def test_dup(self):
        p1 = Predicate("name is 'Jill'")
        s = OptimizedPredicateSet([p1, p1])
        match = s.evaluate({'name': 'Jill'})
        assert match == [p1]

    def test_invalidate(self):
        "AST is invalidated when set changes"
        p1 = Predicate("name is 'Jack'")
        p2 = Predicate("name is 'Jill'")
        s = OptimizedPredicateSet([p1, p2])
        match = s.evaluate({'name': 'Jill'})
        assert match == [p2]

        p3 = Predicate("name is 'Joe'")
        s.add(p3)
        assert s.ast == None
        match = s.evaluate({'name': 'Joe'})
        assert match == [p3]

    def test_finalize(self):
        p1 = Predicate("name is 'Jack'")
        p2 = Predicate("name is 'Jill'")
        s = OptimizedPredicateSet([p1, p2])
        s.finalize()
        match = s.evaluate({'name': 'Jill'})
        assert match == [p2]

        p3 = Predicate("name is 'Joe'")
        with pytest.raises(Exception):
            s.add(p3)

