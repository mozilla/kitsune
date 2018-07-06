#!/bin/sh

echo "$GIT_SHA" > static/revision.txt

# https://stackoverflow.com/questions/25737589/gunicorn-doesnt-log-real-ip-from-nginx
# GUNICORN_LOGFORMAT='%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %({X_Forwarded_For}i)s"'

# exec gunicorn wsgi.app --access-logformat "${GUNICORN_LOGFORMAT}" --config wsgi/config.py

exec uwsgi --http "0.0.0.0:${PORT:-8000}" \
           --processes "${WSGI_NUM_WORKERS:-2}" \
           --harakiri 20 \
           --max-requests 5000 \
           --async 10 \
           --ugreen \
           --master \
           --vacuum \
           --wsgi-file /app/wsgi/app.py \
           --pidfile /tmp/kitsune-master.pid \
           --chdir /app/
