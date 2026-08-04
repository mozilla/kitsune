#!/bin/bash

# set test environment variables
source bin/test-env.sh

set -ex

# wait on database in DATABASE_URL to be ready
urlwait

# Exclude the "es" tag: there is no Elasticsearch here, so a test that needs one must not run
# in this job. Without this, an ES-tagged test added to one of these apps fails on DNS rather
# than being routed to the Elasticsearch job.
./manage.py test --noinput --force-color --timing --parallel=auto --exclude-tag es --exclude-tag no_parallel $@
./manage.py test --noinput --force-color --timing --exclude-tag es --tag no_parallel $@
