#!/bin/bash

READ_ONLY=$(echo "${READ_ONLY:-false}" | tr '[:upper:]' '[:lower:]')

if [[ "$READ_ONLY" == "false" ]]; then
    python manage.py migrate --noinput
fi
