web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120 --access-logfile - --error-logfile -
worker: celery -A config worker --beat --loglevel=info --concurrency=2
