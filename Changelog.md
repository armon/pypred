# Changelog

## 0.3.6

* Improve the optimization of LiteralSet by making sets as small as possible,
and avoiding branches on low density sets.
* SHA: e8dbdb4

## 0.3.5

* Added Literal Set support. This allows for sane contains with a literal
  collection of Literal, Number, or Constant values.
* SHA: 5a2d4f1

## 0.3.0

* Fixed optimizer to handle missing cases
* Internal change to use EvalContext instead of passing around multiple objects
* .analyze() now return the EvalContext instead of a dict
* Duplicate expressions are cached to avoid wasted re-evaluations. This allows
  expressions with low selectivity to still avoid being re-evaluated, even though
  they are not in a branch.
* Export ast.Undefined from the pypred package, since it is generally useful
  for writing custom resolvers.
* SHA: 7d44ae4


## 0.2.2

* NegateOperator provides failure information
* SHA: dd79246

## 0.2.1

* Optimizations for memory utilization
* Input predicates are no longer deep copied (bug fix)
* Fix bug with compiling an empty set
* SHA: f645507

## 0.2.0

* Added `PredicateSet` and `OptimizedPredicateSet` for evaluation
of multiple predicates.
* SHA: 001de5d

## 0.1.1

* Literal resolution caches value so that analyze() output is
  sensible given non-deterministic resolution.
* SHA: ed4c905

## 0.1.0

* Initial release
* SHA: 84e19f5

