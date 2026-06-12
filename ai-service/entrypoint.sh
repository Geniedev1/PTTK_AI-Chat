#!/bin/bash

set -e

GUNICORN_WORKERS="${GUNICORN_WORKERS:-1}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-60}"

echo "Starting ai service..."
exec gunicorn ai_service.wsgi:application --bind 0.0.0.0:8007 --workers "$GUNICORN_WORKERS" --timeout "$GUNICORN_TIMEOUT"
