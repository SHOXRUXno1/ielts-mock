#!/bin/sh
set -e

cd /app
export PYTHONPATH=/app

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec gunicorn -c gunicorn.conf.py app.main:app
