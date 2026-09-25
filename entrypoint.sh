#!/bin/sh
set -e

echo "Waiting for PostgreSQL database..."
if [ "$DB_HOST" ]; then
    while ! nc -z $DB_HOST ${DB_PORT:-5432}; do
      sleep 0.5
    done
    echo "PostgreSQL is ready!"
fi

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

exec "$@"
