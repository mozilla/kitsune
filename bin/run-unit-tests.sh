#!/bin/bash

# set test environment variables
source bin/test-env.sh

set -ex

# wait on database in DATABASE_URL to be ready
urlwait

# wait for elasticsearch to be ready
urlwait http://elasticsearch:9200 60

# ES fixtures initialize their own indices; workers isolate indices and retrieval leases.
# Keep only explicitly marked tests in the serial pass.
./manage.py test --noinput --force-color --timing --parallel=auto --exclude-tag no_parallel "$@"
./manage.py test --noinput --force-color --timing --tag no_parallel "$@" --parallel=1
