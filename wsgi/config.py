# see http://docs.gunicorn.org/en/latest/configure.html#configuration-file

from os import getenv

bind = "0.0.0.0:{}".format(getenv("PORT", 8000))
workers = int(getenv("WSGI_NUM_WORKERS", 5))
accesslog = "-"
errorlog = "-"
loglevel = getenv("WSGI_LOG_LEVEL", "info")
keepalive = int(getenv("WSGI_KEEP_ALIVE", 2))
worker_class = getenv("GUNICORN_WORKER_CLASS", "gevent")
reload = getenv("DEV", False)
