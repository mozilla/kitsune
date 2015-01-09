#!/bin/bash

SUITE=${1:-all}

case $SUITE in
    all )
        scripts/travis/test.sh
        scripts/lint.sh
        ;;
    lint )
        scripts/lint.sh
        ;;
    django )
        scripts/travis/test.sh
        ;;
    * )
        echo "Unknown test suite '$SUITE'."
        exit 1
esac
