#!/bin/bash

# unset all environment variables which have been set in .env file
unset $(sed -n -e 's/^\s*\([^#][^=]*\)=.*/\1/p' .env)

# set environment variables from .env-test file
set -o allexport
source .env-test
set +o allexport

set -ex

# wait on database in DATABASE_URL to be ready
urlwait

# wait for elasticsearch to be ready
urlwait http://elasticsearch7:9200 60

./manage.py es7_init --migrate-writes --migrate-reads

./manage.py test --noinput --force-color --timing
