#!/usr/bin/env bash
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python -m waitress --port="$PORT" config.wsgi:application
