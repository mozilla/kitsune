#!/bin/bash

# set test environment variables
source bin/test-env.sh

set -ex

# wait on database in DATABASE_URL to be ready
urlwait

# wait for elasticsearch to be ready
urlwait http://elasticsearch:9200 60

./manage.py es_init --migrate-writes --migrate-reads

# Run tests that don't write to the shared Elasticsearch index in parallel, then
# run the ES tests serially since parallel workers would collide on the index.
./manage.py test --noinput --force-color --timing --parallel=auto --exclude-tag es --exclude-tag no_parallel $@
./manage.py test --noinput --force-color --timing --tag es --tag no_parallel $@
