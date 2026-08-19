"""Gunicorn config for production (uvicorn workers + single background owner).

Usage (from backend/):
  gunicorn -c gunicorn.conf.py app.main:app
"""

import multiprocessing
import os

bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
# 2–4 workers is enough for ~15 concurrent students; pool_size=20 covers the rest.
workers = int(os.getenv("GUNICORN_WORKERS", max(2, min(4, multiprocessing.cpu_count()))))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "180"))
keepalive = 5
graceful_timeout = 30
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
