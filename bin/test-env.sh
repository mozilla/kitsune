#!/bin/bash

# run `source bin/test-env.sh` to set test environment variables in local shell
# useful for debugging, etc.

# unset all environment variables which have been set in .env file
unset $(sed -n -e 's/^\s*\([^#][^=]*\)=.*/\1/p' .env)

# set environment variables from .env-test file
set -o allexport
source .env-test
set +o allexport
