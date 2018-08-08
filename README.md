PyPred
======
[![Build Status](https://travis-ci.org/armon/pypred.png)](https://travis-ci.org/armon/pypred)

PyPred is a package to do predicate evaluation in Python. It uses a
PLY (Lex/Yacc for Python) to parse inputs into an AST tree which it
then evaluates. The PyPred provides simple APIs to do the evaluation
is most sitations, but allows for customized evaluation techniques for
more complex situations.

Additionally, PyPred supports the notion of predicate "sets". This is
a collection of predicates that are all simultaneously evaluated against
a single input document. For example, in a Pub/Sub system, each subscription
can be modeled as a predicate. When a new event arrives, the predicate set
of all subscriptions can be evaluated to find all matching subscriptions.

PyPred provides a PredicateSet model as well as an OptimizedPredicateSet.
The optimized variant trades memory for speed. It extracts common
sub-expressions into a branch, and conditionally executes different sets
of predicates to prune the predicates that will not match most efficiently.
The parameters of the optimization can be tweaked to find a speed/memory
balance.

Grammar
=======

The grammar that PyPred understands is limited to simple comparisons
and boolean logic.

It supports the following:

* Logical operators `not`, `and`, `or`
* Comparison operators >, >=, <, <=, =, !=, 'is', 'is not'
* Parenthesis to disambiguate
* The subset check operator `contains`
* The regular expression matcher `matches`
* String literals, quoted if they include spaces
* Numeric literals
* Constants true, false, undefined, null, empty
* Set literal, containing string literals, numeric and constant values

Grammar Examples
================

To demonstate the capabilities of the pypred grammar, the following
examples are provided.

    name is 'Jack' and friend_name is 'Jill'

This predicate checks that the input document has a field name equal to
"Jack", and a field friend\_name equal to "Jill"

    event is "Record Score" and ((score >= 500 and highest_score_wins) or (score < 10 and lowest_score_wins))

This is a slightly more advanced predicate. It checks that this is a "Record Score" event,
and that the score is either greater than or equal to 500 in the case that a high score is desireable,
or that the score is less than 10 if a low score is desirable.

    server matches "east-web-([\d]+)" and errors contains "CPU load" and environment != test

This checks for any webserver hostname matching a numeric suffix, such as "east-web-001", with
"CPU load" being reported as an error in a non-test environment.

If you want to use regular expression with modifiers, you can try out the following example:

    haiku matches /^my life,\s-.How much.*brief\.$/mis

This regular expression will match the following haiku:

    My life, -
    How much more of it remains?
    The night is brief.

Notice that in previous example we used slashes instead of quotation marks. This allowed us to set modifiers (after slashes). This behaviour is very similar to Javascript regular expressions. Supported modifiers are:

* _i_ (ignore case)
* _m_ (multiline)
* _s_ (dotall)
* _u_ (unicode)
* _l_ (locale)

Literal sets can be used to check for multiple clauses:

    {"WARN" "ERR" "CRIT"} contains error_level or {500 501 503} contains status_code

This provides two literal sets which are used to check against the dynamic values
of error\_level and status\_code.

API
===

Predicates themselves have a single interface, which is the `Predicate` class.
It is instantiated with a string predicate.

The main API's for it are:
* Predicate(Pred) : Creates a new predicate object

* Predicate.description(): Returns a human readable version of the tree if valid

* Predicate.is\_valid() : Returns if the predicate is valid

* Predicate.errors(): If not valid, returns a list of tokenization, syntax, and semantic errors

* Predicate.evaluate(document) : Evaluates the given document against the predicate

* Predicate.analyze(document) : Evaluates the given document against the predicate,
  returns the results, as well as the evaluation context that includes more information about
  the evaluation, including the failure reasons. This is generally much slower than
  evaluate in the failure cases.

One of the critical aspects of evaluating a predicate is the resolution of
literals. When the AST needs a value to substitute a variable, it calls the
`resolve_identifier` method of the Predicate. The default behavior is flexible,
and support string literals, dictionary lookups, nested dictionaries, and
call back resolution via `set_resolver`. However, if a client wants to customize
the resolution of identifier, they can simply override this method.

Predicate Sets have two main interfaces, either the `PredicateSet` or `OptimizedPredicateSet`.

Both share part a subset of their calls:

* Set(preds=None) : Instantiate the set, optionally with a list of predicates

* Set.add(predicate) : Adds a predicate to the set

* Set.update(predicates) : Extends to include a list of predicates

* Set.evaluate(document) : Evaluates the document against the predicates and returns a list of matches

The OptimizedPredicateSet supports an extended set of API's:

* OptSet.description() : Returns ahuman readable version of the optimized tree

* OptSet.analyze(document) : Like Predicate.analyze(), but returns a boolean, a list, and the evaluation context.

* OptSet.compile\_ast() : Forces compilation of the interal AST

* OptSet.finalize() : Prunes the AST of sub-predicates, and removes any instance data that is not used
  as part of the evaluation of the optimized set. Not usually needed, but can reduce the total memory
  footprint, and is useful if the object is going to be pickled.

The standard PredicateSet relies on the underlying predicates to do
resolution of literals, however the OptimizedPredicateSet implements
`resolve_identifier` to do so. Thus if custom behavior is wanted, the
optimized set must be sub-classed.


Human Readable Outputs
======================

PyPred tries to make it possible to provide human readable output of
both predicates as well as any error messages that are encountered.
Here is an example of a human readable description of:

    p = Predicate('server matches "east-web-([\d]+)" and errors contains "CPU load" and environment != test')
    print p.description()

    AND operator at line: 1, col 34
        MatchOperator at line: 1, col 7
            Literal server at line: 1, col 0
            Regex 'east-web-([\\d]+)' at line: 1, col 15
        AND operator at line: 1, col 65
            ContainsOperator at line: 1, col 45
                Literal errors at line: 1, col 38
                Literal "CPU load" at line: 1, col 54
            != comparison at line: 1, col 81
                Literal environment at line: 1, col 69
                Literal test at line: 1, col 84

Here is an example of the output during a failed evaluation:

    p = Predicate('server matches "east-web-([\d]+)" and errors contains "CPU load" and environment != test')
    res, ctx = p.analyze({'server': 'east-web-001', 'errors': [], 'environment': 'prod'})
    assert res == False

    pprint.pprint(ctx.failed)
     ["Right side: 'CPU load' not in left side: [] for ContainsOperator at line: 1, col 45",
                 'Left hand side of AND operator at line: 1, col 65 failed',
                 'Right hand side of AND operator at line: 1, col 34 failed']

    pprint.pprint(ctx.literals)
     {'"CPU load"': 'CPU load',
      'errors': [],
      'server': 'east-web-001'}

