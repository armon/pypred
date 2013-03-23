import time
import random
random.seed(1)
from pypred import Predicate, PredicateSet, OptimizedPredicateSet

def get_words():
    "Returns a large list of words"
    raw = open("/usr/share/dict/words").readlines()
    return [r.strip() for r in raw]

def get_names():
    "Returns a large list of names"
    raw = open("/usr/share/dict/propernames").readlines()
    return [r.strip() for r in raw]

NAMES = get_names()
WORDS = get_words()
SELECT_NAMES = random.sample(NAMES, 1000)
SELECT_WORDS = random.sample(WORDS, 1000)


def timed(f):
    def wrapper(*args, **kwargs):
        s = time.time()
        r = f(*args, **kwargs)
        e = time.time()
        print "Spent %0.3f sec invoking %s" % (e-s, f.func_name)
        return r
    return wrapper


@timed
def gen_predicates(num):
    res = []
    for x in xrange(num):
        r = random.randint(0,5)
        if r == 0:
            p_str = "name is '%s' and not test" % random.choice(SELECT_WORDS)
        elif r == 1:
            gender = "Male" if random.random() > 0.5 else "Female"
            age = random.randint(1, 100)
            p_str = "gender is '%s' and age > %d" % (gender, age)
        elif r == 2:
            city_letter = chr(97+random.randint(0, 25))
            city_reg = "^%s.*" % city_letter
            age = random.randint(1, 100)
            p_str = "age > %d and city matches '%s'" % (age, city_reg)
        elif r == 3:
            interest = random.choice(SELECT_WORDS)
            p_str = "interests contains '%s' and test" % interest
        elif r == 4:
            gender = "Male" if random.random() else "Female"
            p_str = "name is '%s' or gender is '%s'" % (random.choice(SELECT_WORDS), gender)
        elif r == 5:
            gender = "Male" if random.random() else "Female"
            age = random.randint(1, 100)
            p_str = "(age > %d and gender is '%s')" % (age, gender)
            gender = "Male" if random.random() else "Female"
            age = random.randint(1, 100)
            p_str += " or (age < %d and gender is '%s')" % (age, gender)

        p = Predicate(p_str)
        res.append(p)
    return res

@timed
def gen_docs(num):
    res = []
    for x in xrange(num):
        interests = [random.choice(SELECT_WORDS) for x in xrange(3)]
        city = random.choice(WORDS)
        age = random.randint(1, 100)
        test = True if random.random() > 0.5 else False
        gender = "Male" if random.random() > 0.5 else "Female"
        d = {'name': random.choice(SELECT_NAMES), 'interests': interests, 'city': city, 'age':age, 'gender': gender, 'test': test}
        res.append(d)
    return res

@timed
def make_set(preds):
    return PredicateSet(preds)

@timed
def make_set_optimized(preds):
    s = OptimizedPredicateSet(preds)
    s.compile_ast()
    #print s.ast.description()
    return s

def main(numpreds=1000, numdocs=2000, printp=0):
    preds = gen_predicates(numpreds)
    docs = gen_docs(numdocs)
    s1 = make_set(preds)
    s2 = make_set_optimized(preds)

    if printp:
        print "Predicates:"
        for p in preds:
            print "\t", p.predicate

    # Time the evaluation
    start = time.time()
    total = 0
    for d in docs:
        total += len(s1.evaluate(d))
    end = time.time()
    print "(Naive) Evaluated %d docs across %d predicates in %0.3f seconds" % (numdocs, numpreds, end-start)
    print "(Naive) Total of %d predicates matched" % total

    # Time the evaluation
    start = time.time()
    total_o = 0
    for d in docs:
        total_o += len(s2.evaluate(d))
    end = time.time()
    print "(Opt) Evaluated %d docs across %d predicates in %0.3f seconds" % (numdocs, numpreds, end-start)
    print "(Opt) Total of %d predicates matched" % total_o

    if total != total_o:
        print "Mismatch! Differing inputs:"
        for d in docs:
            r1 = s1.evaluate(d)
            r2 = s2.evaluate(d)
            if r1 != r2:
                print "Input:",repr(d)
                print "Naive:"
                for p in r1:
                    print "\t",p.predicate
                print "Opt:"
                for p in r2:
                    print "\t",p.predicate
                print



if __name__ == "__main__":
    main()

