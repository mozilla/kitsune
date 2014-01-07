#!/bin/bash

# This file runs a serious of lints against the code base, each of which
# has been configured to our liking. This is intended to be run as part
# of a continuous integration suite, and all new code should pass these
# tests. The currently run lint programs are:
#
# - pep8
# - pyflakes
#
# Generated code such as migrations are ignored, as are any other files
# that would be unreasonable to lint. Think carefully before adding a
# new file to the list of ignores.

FLAKE8_IGNORE=(
    'migrations'
    'kitsune/settings*'
    'kitsune/sumo/db_strings.py'
    'kitsune/sumo/static/js/libs/ace/kitchen-sink/docs/python.py'
)

FLAKE8_IGNORE=$(IFS=,; echo "${FLAKE8_IGNORE[*]}")
flake8 --exclude=$FLAKE8_IGNORE kitsune
FLAKE_RETURN=$?

exit $FLAKE_RETURN
