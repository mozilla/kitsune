#!/bin/sh

echo "$GIT_SHA" > static/revision.txt

# https://stackoverflow.com/questions/25737589/gunicorn-doesnt-log-real-ip-from-nginx
GUNICORN_LOGFORMAT='%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" %({X_Forwarded_For}i)s"'

exec gunicorn wsgi.app --access-logformat "${GUNICORN_LOGFORMAT}" --config wsgi/config.py
