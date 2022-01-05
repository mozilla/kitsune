# see http://docs.gunicorn.org/en/latest/configure.html#configuration-file

from os import getenv

bind = "0.0.0.0:{}".format(getenv("PORT", 8000))
workers = int(getenv("WSGI_NUM_WORKERS", 2))
threads = int(getenv("WSGI_NUM_THREADS", 4))
worker_tmp_dir = getenv("WSGI_WORKER_TMP_DIR", "/dev/shm")
accesslog = "-"
errorlog = "-"
loglevel = getenv("WSGI_LOG_LEVEL", "info")
keepalive = int(getenv("WSGI_KEEP_ALIVE", 2))
worker_class = getenv("GUNICORN_WORKER_CLASS", "gevent")
reload = getenv("DEV", False)
