#!/bin/bash

set -ex

./node_modules/.bin/mocha --require ./webpack/mocha-require --recursive kitsune/*/static/*/js/tests/* $@
