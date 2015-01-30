from pypred import util

class TestUtil(object):
    def test_mode(self):
        "Tests mode selection"
        v = [1,2,3,5,5,5,4,3,1]
        assert 5 == util.mode(v)

    def test_median(self):
        "Tests mode selection"
        v = list(range(0, 100))
        assert 50 == util.median(v)

    def test_max_count(self):
        "Tests the max count"
        d = {
            "foo": 10,
            "bar": 20,
            "zip": 30,
            "zoo": 4
        }
        gen = util.max_count(d)
        assert ((30, "zip") == next(gen))
        assert ((20, "bar") == next(gen))
        assert ((10, "foo") == next(gen))
        assert ((4, "zoo") == next(gen))

    def test_harmonic_mean(self):
        "Tests the hamronic mean"
        v = [1,2,3,4,5,6,7,8,9,10]
        m = util.harmonic_mean(v)
        assert int(m * 1000) == 3414

        v = [0.01, 0.01, 0.2, 0.2, 0.3, 0.01]
        m = util.harmonic_mean(v)
        assert int(m * 1000) == 19

