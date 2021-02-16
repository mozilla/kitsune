#!/bin/bash

set -ex

./node_modules/.bin/mocha --require @babel/register --recursive kitsune/*/static/*/js/tests/* $@
