#!/bin/bash

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
    1.5*|1.6*|6.0*)
        echo "peep.sh: Wheel-using pip detected, so passing --no-use-wheel."
        ARGS="--no-use-wheel"
        ;;
    6.1*)
        echo
        echo "Error: peep does not support pip >= 6.1."
        echo "Please downgrade your version of pip by running:"
        echo ""
        echo "    pip install --upgrade 'pip<6.1'"
        exit 1
esac

# Execute peep with the command line args plus the additional args
# if any.
python ./bin/peep-2.2.py "$@" $ARGS

echo "peep.sh: Done!"
