#!/bin/bash

set -e

echo "Waiting for database connection..."
MAX_ATTEMPTS=30
ATTEMPT=0
until python -c "import django; django.setup()" > /dev/null 2>&1 || [ $ATTEMPT -eq $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: Waiting for database..."
    sleep 1
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "Database connection timeout"
fi

echo "Running migrations..."
python manage.py migrate --noinput || true

GUNICORN_WORKERS="${GUNICORN_WORKERS:-1}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-60}"

echo "Starting product service..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8004 --workers "$GUNICORN_WORKERS" --timeout "$GUNICORN_TIMEOUT"
