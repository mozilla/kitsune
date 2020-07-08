#!/bin/bash

newrelic-admin run-program celery -A kitsune worker -Q fxa -Ofair -n fxa@%h --maxtasksperchild=${CELERY_WORKER_MAX_TASKS_PER_CHILD:-25} &
exec newrelic-admin run-program celery -A kitsune worker -Q deafult -n default@%h --maxtasksperchild=${CELERY_WORKER_MAX_TASKS_PER_CHILD:-25} &
