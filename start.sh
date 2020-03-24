#!/bin/bash
python manage.py makemigrations &&
python manage.py migrate &&
python manage.py collectstatic &&
gunicorn --config gunicorn.conf shima.wsgi:application
