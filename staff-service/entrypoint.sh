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

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput || true

# Create superuser
python manage.py shell << END
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Superuser created")
END

GUNICORN_WORKERS="${GUNICORN_WORKERS:-1}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-60}"

# Start server
echo "Starting staff service..."
exec gunicorn staff_service.wsgi:application --bind 0.0.0.0:8001 --workers "$GUNICORN_WORKERS" --timeout "$GUNICORN_TIMEOUT"
