#!/bin/bash

set -e

# Wait for database with timeout
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

echo "Starting cart service..."
exec gunicorn cart_service.wsgi:application --bind 0.0.0.0:8003 --workers 4
