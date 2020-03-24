#!/bin/bash
python manage.py makemigrations &&
python manage.py migrate &&
python manage.py collectstatic --noinput &&
gunicorn --config gunicorn.conf shima.wsgi:application
