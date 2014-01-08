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

# Files to lint is either the list of arguments to this script, or the
# kitsune directory.
FILES="$@"

FLAKE8_FILES=()
for f in $FILES; do
    # If it is a directory, or if it is a python file, lint it with flake8.
    if [[ -d $f ]] || echo $f | grep -E '.py$' > /dev/null; then
        FLAKE8_FILES+=($f)
    fi
done
FLAKE8_IGNORE=$(IFS=,; echo "${FLAKE8_IGNORE[*]}")

# If there are files to run through flake8, do it.
if [[ -n ${FLAKE8_FILES[*]} ]]; then
  flake8 --exclude=$FLAKE8_IGNORE ${FLAKE8_FILES[*]}
  FLAKE_RETURN=$?
else
  FLAKE_RETURN=0
fi

exit $FLAKE_RETURN
