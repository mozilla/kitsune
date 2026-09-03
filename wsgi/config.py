# see http://docs.gunicorn.org/en/latest/configure.html#configuration-file

from os import getenv

wsgi_app = "wsgi.app:application"
bind = f"0.0.0.0:{getenv('PORT', 8000)}"
workers = int(getenv("WSGI_NUM_WORKERS", 3))
worker_tmp_dir = getenv("WSGI_WORKER_TMP_DIR", "/dev/shm")
accesslog = "-"
errorlog = "-"
loglevel = getenv("WSGI_LOG_LEVEL", "info")
worker_class = getenv("GUNICORN_WORKER_CLASS", "sync")
reload = getenv("DEV", False)
# Leave this off (gunicorn's default is off too). This comment explains why.
# From gunicorn 24 on, SO_REUSEPORT gives every worker its own listening socket
# and its own queue of waiting connections. When a worker exits -- usually after
# WSGI_MAX_REQUESTS requests -- its queue is thrown away and everything still
# waiting in it gets cut off, which nginx reports as a 502.
reuse_port = False
keepalive = int(getenv("WSGI_KEEP_ALIVE", 60))
timeout = int(getenv("WSGI_TIMEOUT", 30))
graceful_timeout = int(getenv("WSGI_GRACEFUL_TIMEOUT", 10))
max_requests = getenv("WSGI_MAX_REQUESTS", 1300)
max_requests_jitter = getenv("WSGI_MAX_REQUESTS_JITTER", 30)
control_socket_disable = True
