PyPred
======

PyPred is a package to do predicate evaluation in Python. It uses a
PLY (Lex/Yacc for Python) to parse inputs into an AST tree which it
then evaluates. The PyPred provides simple APIs to do the evaluation
is most sitations, but allows for customized evaluation techniques for
more complex situations.

Grammer
=======

The grammer that PyPred understands if fairly limited, and is restricted
to boolean logic.

It supports the following:

* Logical operators `not`, `and`, `or`
* Comparison operators >, >=, <, <=, =, !=, 'is', 'is not'
* Parenthesis to disambiguate
* The subset check operator `contains`
* The regular expression matcher `matches`
* String literals, quoted if they include spaces
* Numeric literals
* Constants true, false, undefined, null, empty

Grammer Examples
================

To demonstate the capabilities of the pypred grammer, the following
examples are provided.

    name is Jack and friend_name is Jill

This predicate checks that the input document has a field name equal to
"Jack", and a field friend\_name equal to "Jill"

    event is "Record Score" and ((score >= 500 and highest_score_wins) or (score < 10 and lowest_score_wins))

This is a slightly more advanced predicate. It checks that this is a "Record Score" event,
and that the score is either greater than or equal to 500 in the case that a high score is desireable,
or that the score is less than 10 if a low score is desirable.

    server matches "east-web-([\d]+)" and errors contains "CPU load" and environment != test

This checks for any webserver hostname matching a numeric suffix, such as "east-web-001", with
"CPU load" being reported as an error in a non-test environment.

API
===

Using the pypred package is very simple as well. It has a single primary
interface, which is the `Predicate` class. It is instantiated with
a string predicate.

The main interface for it is:
* Predicate(Pred) : Creates a new predicate object

* Predicate.is\_valid() : Returns if the predicate is valid

* Predicate.parse\_errors(): If not valid, returns a list of parse errors

* Predicate.evaluate(document) : Evaluates the given document against the predicate,
  returns the result of the evaluation

* Predicate.analyze(document) : Evaluates the given document against the predicate,
  returns the results, as well as a dictionary that includes more information about
  the evaluation, including the failure reasons



