from pypred import util

class TestUtil(object):
    def test_mode(self):
        "Tests mode selection"
        v = [1,2,3,5,5,5,4,3,1]
        assert 5 == util.mode(v)

    def test_median(self):
        "Tests mode selection"
        v = list(xrange(0, 100))
        assert 50 == util.median(v)

    def test_max_count(self):
        "Tests the max count"
        d = {
            "foo": 10,
            "bar": 20,
            "zip": 30,
            "zoo": 4
        }
        assert 30, "zip" == util.max_count(d)

