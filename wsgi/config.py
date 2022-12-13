# see http://docs.gunicorn.org/en/latest/configure.html#configuration-file

from os import getenv

wsgi_app = "wsgi.app:application"
bind = f"0.0.0.0:{getenv('PORT', 8000)}"
workers = int(getenv("WSGI_NUM_WORKERS", 4))
worker_tmp_dir = getenv("WSGI_WORKER_TMP_DIR", "/dev/shm")
accesslog = "-"
errorlog = "-"
loglevel = getenv("WSGI_LOG_LEVEL", "info")
keepalive = int(getenv("WSGI_KEEP_ALIVE", 2))
worker_class = getenv("GUNICORN_WORKER_CLASS", "gevent")
reload = getenv("DEV", False)
timeout = int(getenv("WSGI_TIMEOUT", 30))
graceful_timeout = int(getenv("WSGI_GRACEFUL_TIMEOUT", 30))
worker_connections = int(getenv("WSGI_WORKER_CONNECTIONS", 5))
# improve fairness 
reuse_port = getenv("WSGI_REUSE_PORT", True)
