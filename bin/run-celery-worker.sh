#!/bin/bash

exec newrelic-admin run-program celery -A kitsune worker --max-tasks-per-child=${worker_max_tasks_per_child:-25}
