#!/bin/sh

./bin/run-common.sh

echo "$GIT_SHA" > static/revision.txt

exec gunicorn kitsune.wsgi.app --config wsgi/config.py
