#!/bin/bash

RUN_MIGRATE=$(echo "${RUN_MIGRATE:-false}" | tr '[:upper:]' '[:lower:]')

if [[ "$RUN_MIGRATE" == "true" ]]; then
    python manage.py migrate --noinput
fi
