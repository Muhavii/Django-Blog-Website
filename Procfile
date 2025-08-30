web: python manage.py migrate && python manage.py collectstatic --noinput && python manage.py create_superuser && gunicorn myproject.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --workers 2
