#!/bin/bash

# Get the queue name from the first argument, otherwise default to "celery".
QUEUE="${1:-celery}"

# If the queue is "email", force the concurrency to a single process.
if [ "$QUEUE" = "email" ]; then
    CONCURRENCY="--concurrency 1"
else
    CONCURRENCY=""
fi

exec celery -A kitsune worker -Q $QUEUE $CONCURRENCY --loglevel INFO --max-tasks-per-child=${CELERY_WORKER_MAX_TASKS_PER_CHILD:-25}
