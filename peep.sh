#!/bin/bash

set -eu

# Get pip version number
PIPVER=`pip --version | awk '{print $2}'`
ARGS=""

echo "peep.sh: Using pip $PIPVER"

# If we're using pip 1.5, 1.6 or 6.0, then toss on the --no-use-wheel
# argument.
#
# Note: If we encounter other versions of pip here that require other
# things, we can toss them in.
case $PIPVER in
    1.5*|1.6*|6.*)
        echo "peep.sh: Wheel-using pip detected, so passing --no-use-wheel."
        ARGS="--no-use-wheel"
        ;;
esac

# Execute peep with the command line args plus the additional args
# if any.
python ./scripts/peep.py "$@" $ARGS

echo "peep.sh: Done!"
