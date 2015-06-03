#!/bin/bash

SUITE=${1:-all}

case $SUITE in
    all )
        scripts/travis/test.sh
        pre-commit run --all-files
        ;;
    lint )
        pre-commit run --all-files
        ;;
    django )
        scripts/travis/test.sh
        ;;
    * )
        echo "Unknown test suite '$SUITE'."
        exit 1
esac
