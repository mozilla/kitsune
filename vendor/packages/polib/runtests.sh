#!/bin/sh
if which coverage > /dev/null; then
    coverage run tests/tests.py
    coverage report
else
    /usr/bin/env python tests/tests.py
fi
