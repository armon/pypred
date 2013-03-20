from pypred import PredicateSet, Predicate

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

