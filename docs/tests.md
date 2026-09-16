---
title: All about testing
---

!!! warning

    This section of documentation may be outdated.


Kitsune has a fairly comprehensive Python test suite. Changes should not
break tests—only change a test if there is a good reason to change
the expected behavior—and new code should come with tests.

# Running the Test Suite

If you followed the steps in [the installation docs](hacking_howto.md),
then you should be all set setup-wise.

To run the tests, you need to do:

    ./manage.py test

That doesn't provide the most sensible defaults for running the tests.
Here is a good command to alias to something short:

    ./manage.py test -s --noinput --logging-clear-handlers

The `-s` flag is important if you want to be able to drop into PDB from
within tests.

Some other helpful flags are:

`-x`:

:   Fast fail. Exit immediately on failure. No need to run the whole
    test suite if you already know something is broken.

`--pdb`:

:   Drop into PDB on an uncaught exception. (These show up as `E` or
    errors in the test results, not `F` or failures.)

`--pdb-fail`:

:   Drop into PDB on a test failure. This usually drops you right at the
    assertion.

`--no-skip`:

:   All SkipTests show up as errors. This is handy when things
    shouldn't be skipping silently with reckless abandon.

## Running a Subset of Tests

You can run part of the test suite by specifying the apps you want to
run, like:

    ./manage.py test kitsune/wiki kitsune/search kitsune/kbforums

You can also specify modules:

    ./manage.py test kitsune.wiki.tests.test_views

You can specify specific tests:

    ./manage.py test kitsune.wiki.tests.test_views:VersionGroupTests.test_version_groups

See the output of `./manage.py test --help` for more arguments.

## Parallel tests

The test runner selects the `spawn` multiprocessing method before Django resolves
`--parallel=auto`. This avoids a silent fallback to one worker when the platform
defaults to `forkserver`.

`--parallel=auto` uses `DJANGO_TEST_PROCESSES` when set, otherwise the CPU count.
An explicit `--parallel=N` takes precedence over that environment variable;
`--parallel=1` runs serially. Django may reduce the worker count when there are
fewer test classes than requested workers.

CI sets `DJANGO_TEST_PROCESSES=2` in `docker/docker-compose.ci.yml` to match its
current CPU allocation without depending on host CPU discovery. Update that
limit when changing CI resources.

For example, to limit an automatic run to two workers:

    docker compose run --rm -e DJANGO_TEST_PROCESSES=2 web ./manage.py test kitsune.users --parallel=auto

Spawned workers use a process-local default cache while preserving the other
cache aliases as configured, and use the same fast password hashing as serial tests.
The development dependencies include `tblib` so failures in workers retain their
tracebacks. The CI scripts continue to run ES and `no_parallel` tests serially.

## CI test image

The Docker `test` target reuses the compiled gettext catalogs, JavaScript
catalogs, and `postatus.txt` from `jsi18n-generator`. This keeps the frontend
and test image on the same translation snapshot instead of fetching and
compiling translations twice.

It still runs `collectstatic` with `.env-test`. Keep `postatus.txt` alongside
the catalogs when changing this build: it is part of the collected static files.

## CI partition coverage

The CircleCI `kitsune-tests` job runs `check_test_partitions` before its tests.
The command uses Django's test runner to discover test IDs under `kitsune` and
compare them with the app labels of the test jobs scheduled in `.circleci/config.yml`.
It fails on missing tests, overlapping partitions, or discovery errors. A job
definition that is absent from the workflows does not count toward coverage.

The check accounts for both passes of the test scripts: no-ES jobs exclude
`es`-tagged tests, including tests also tagged `no_parallel`. Keep the command's
tag handling in sync when changing `bin/run-unit-tests.sh` or
`bin/run-unit-tests-no-es.sh`.

To run the check in the development environment:

    docker compose run --rm web ./manage.py check_test_partitions

Use `--config PATH` to check an alternative CircleCI configuration. The check
imports tests but does not execute them or create a test database.

## Running tests without collecting static files

By default the test runner will run `collectstatic` to ensure that all
the required assets have been collected to the static folder. If you do
not want this default behavior you can run:

    REUSE_STATIC=1 ./manage.py test

## The Test Database

The test suite will create a new database named `test_%s` where `%s` is
whatever value you have for `settings.DATABASES['default']['NAME']`.

Make sure the user has `ALL` on the test database as well. This is
covered in the installation chapter.

When the schema changes, you may need to drop the test database. You can
also run the test suite with `FORCE_DB` once to cause Django to drop and
recreate it:

    FORCE_DB=1 ./manage.py test -s --noinput --logging-clear-handlers

# Writing New Tests

Code should be written so it can be tested, and then there should be
tests for it.

When adding code to an app, tests should be added in that app that cover
the new functionality. All apps have a `tests` module where tests should
go. They will be discovered automatically by the test runner as long as
the look like a test.

-   We use "modelmakers" instead of fixtures. Models should have
    modelmakers defined in the tests module of the Django app. For
    example, `forums.tests.document` is the modelmaker for
    `forums.Models.Document` class.

## Password hashing

The Python test runner uses Django's `MD5PasswordHasher` for disposable test
passwords to avoid the cost of production-strength hashing in factories and
logins. This applies to serial and spawned parallel runs, without requiring
`TEST=True`. Application password hashing is unchanged, and the runner restores
the original hashers when it exits, including when it raises an exception.

Tests that exercise a specific password-hashing algorithm should select it with
`django.test.override_settings(PASSWORD_HASHERS=[...])`.

# Changing Tests

Unless the current behavior, and thus the test that verifies that
behavior is correct, is demonstrably wrong, don't change tests. Tests
may be refactored as long as its clear that the result is the same.

# Removing Tests

On those rare, wonderful occasions when we get to remove code, we should
remove the tests for it, as well.

If we liberate some functionality into a new package, the tests for that
functionality should move to that package, too.

# JavaScript Tests

Frontend JavaScript is currently tested with
[Mocha](https://mochajs.org/).

## Running JavaScript Tests

To run tests, make sure you have have the NPM dependencies installed,
and then run:

    npm run webpack:test

## Writing JavaScript Tests

Mocha tests are discovered using the pattern
`kitsune/*/static/*/js/tests/**/*.js`. That means that any app can have
a `tests` directory in its JavaScript directory, and the
files in there will all be considered test files. Files that don't
define tests won't cause issues, so it is safe to put testing utilities
in these directories as well.

Here are a few tips for writing tests:

-   Any HTML required for your test should be added by the tests or a
    `beforeEach` function in that test suite. React is useful for this.
-   You can use `sinon` to mock out parts of libraries or
    functions under test. This is useful for testing AJAX.
-   The tests run in a Node.js environment. A browser environment can be
    simulated using `jsdom`.
