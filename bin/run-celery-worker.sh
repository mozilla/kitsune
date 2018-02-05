#!/bin/bash

exec newrelic-admin run-program python manage.py celeryd --maxtasksperchild=${CELERY_MAX_TASKS_PER_CHILD:-100}
