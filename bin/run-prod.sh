#!/bin/sh

echo "$GIT_SHA" > static/revision.txt

# https://stackoverflow.com/questions/25737589/gunicorn-doesnt-log-real-ip-from-nginx
GUNICORN_LOGFORMAT='%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %({x-forwarded-for}i)s'

exec gunicorn --access-logformat "${GUNICORN_LOGFORMAT}" --config wsgi/config.py
