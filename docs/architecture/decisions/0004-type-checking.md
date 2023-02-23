# 4 - Type Hints and Checking

Date: 2023-02-15

## Status

Pending

## Context

With support for [type hints](https://docs.python.org/3/library/typing.html)
and [static type-checking tools](https://mypy-lang.org/) solidly entrenched in
the Python eco-system, we'd like to take advantage of both within Kitsune. The
goal is to support
[gradual typing](https://peps.python.org/pep-0483/#summary-of-gradual-typing),
to support the addition of type-hints only where they're helpful, where their
addition adds more value than their burden.

Type hints can be helpful to quickly understand the types of values expected by
functions and methods, as well as the types of their results, easing the burden
of using those functions/methods for the first time. It encourages modularity,
since one doesn't have to dig into the details of the underlying code to discover
what's expected. Once in place, they also enable the use of static type-checking
tools, which can flag basic interface errors, for example, when you're passing a
`str` into a function that expects an `int`.

Type hints can sometimes be an undue burden as well. In some cases determining
the correct type can be difficult, time-consuming, and the outcome unintuitive.
In those cases, it's probably better to skip them.

In the end, it's important to remember that type hints and static type-checking
are never a substitute for testing. Writing good tests for your code is essential
whether you add type hints or not.

## Decision

We recommend that all pull requests that modify/create Python functions and/or
methods, add a type hint for each of the function/method arguments as well as the
result. There's a judgement call here though. If it's an "undue burden", skip it.
If not, do it.

Also, we will run a static type-checking tool, either prior to commits, or during
CI, or both.

## Consequences

There are two primary consequences.

- An easier, less error-prone coding experience when working with unfamiliar Python
  functions/methods.

- We reap the benefits of using a static type-checking tool. For example, the
  detection, prior to run time, of interface errors, where the types passed into
  functions/methods or the results returned are not what's expected.

There is the potential for this to have a negative consequence as well. It could slow
us down. It could cost more than its worth. So, it's important to keep in mind the tradeoff. Type hints should only be added where they're helpful.
