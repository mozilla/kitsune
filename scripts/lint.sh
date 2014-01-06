#!/bin/bash

FLAKE8_IGNORE=(
    'migrations'
    'kitsune/settings*'
    'kitsune/sumo/db_strings.py'
    'kitsune/sumo/static/js/libs/ace/kitchen-sink/docs/python.py'
)

FLAKE8_IGNORE=$(IFS=,; echo "${FLAKE8_IGNORE[*]}")
flake8 --exclude=$FLAKE8_IGNORE kitsune
