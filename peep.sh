#!/bin/bash

set -eu

# Get pip version number
PIPVER=`pip --version | awk '{print $2}'`
ARGS=""

echo "peep.sh: Using pip $PIPVER"

# Add pip arguments that vary according to the version of pip, here:
case $PIPVER in
    1.5*|6.*)
        # Pip uses the wheel format packages by default in pip 1.5+.
        # However in pip < 6.0+ wheel support is broken, and even with pip 6.0+
        # we intentionally don't use the wheel packages, since otherwise each
        # package in the requirements files would need multiple hashes.
        echo "peep.sh: Wheel-using pip detected, so passing --no-use-wheel."
        ARGS="--no-use-wheel"
        ;;
    7.*)
        # Pip 7.x is just not compatible with peep.
        echo 'peep.sh: Pip 7.x and above are not compatible with peep.'
        echo 'peep.sh: Please install an earlier version with the command'
        echo "peep.sh: \"pip install -U 'pip<7'\""
        exit 1
        ;;
esac

# Add the version specific arguments to those passed on the command line.
python ./scripts/peep.py "$@" $ARGS

echo "peep.sh: Done!"
