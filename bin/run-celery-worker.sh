#!/bin/bash

exec newrelic-admin run-program celery -A kitsune worker -Q default,fxa  --maxtasksperchild=${CELERY_WORKER_MAX_TASKS_PER_CHILD:-25} &
