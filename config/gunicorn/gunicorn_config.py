# gunicorn_config.py

import multiprocessing

bind = "127.0.0.1:8002"     # Nginx will proxy to this
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended formula
threads = 2
worker_class = "gthread"

# Logging
accesslog = "/var/log/remindly/remindly_access.log"
errorlog = "/var/log/remindly/remindly_error.log"
loglevel = "info"

# Timeout settings
timeout = 30
graceful_timeout = 30
keepalive = 5

