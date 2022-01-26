#!/bin/bash

# set test environment variables
source test-env.sh

set -ex

# wait on database in DATABASE_URL to be ready
urlwait

# wait for elasticsearch to be ready
urlwait http://elasticsearch7:9200 60

./manage.py es7_init --migrate-writes --migrate-reads

./manage.py test --noinput --force-color --timing $@
