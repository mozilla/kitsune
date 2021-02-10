#!/bin/bash

set -ex

# wait on database in DATABASE_URL to be ready
urlwait

./manage.py es7_init --migrate-writes --migrate-reads

./manage.py test --noinput --nologcapture -a '!search_tests' --with-nicedots
