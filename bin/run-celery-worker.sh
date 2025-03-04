#!/bin/bash

exec newrelic-admin run-program celery -A kitsune worker -Q "${1:-celery}" --max-tasks-per-child=${CELERY_WORKER_MAX_TASKS_PER_CHILD:-25}
