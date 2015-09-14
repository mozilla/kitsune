#!/bin/bash

DIR=$(dirname $0)

$DIR/../node_modules/.bin/mocha \
    --compilers js:babel/register \
    --recursive \
    kitsune/*/static/*/js/tests/* \
    "$@"
