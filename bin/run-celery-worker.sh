#!/bin/bash

exec newrelic-admin run-program celery -A kitsune worker -n default@%h --maxtasksperchild=${CELERY_WORKER_MAX_TASKS_PER_CHILD:-25} &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start default worker: $status"
  exit $status
fi

exec newrelic-admin run-program celery -A kitsune worker -Q fxa -n fxa@%h --maxtasksperchild=${CELERY_WORKER_MAX_TASKS_PER_CHILD:-25} &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start fxa worker: $status"
  exit $status
fi
