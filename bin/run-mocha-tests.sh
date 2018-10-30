#!/bin/bash

set -ex

./node_modules/.bin/mocha --compilers js:babel/register --recursive kitsune/*/static/*/js/tests/* $@
