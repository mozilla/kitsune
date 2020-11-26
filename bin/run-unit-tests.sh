#!/bin/bash

set -ex

# wait on database in DATABASE_URL to be ready
urlwait

./manage.py es7_init --delete

./manage.py test --noinput --nologcapture -a '!search_tests' --with-nicedots
