#!/bin/bash

set -e

if [[ "$WAIT_FOR_IT_ADDRESS" ]]; then
    ./wait-for-it.sh $WAIT_FOR_IT_ADDRESS --timeout=30
fi

if [[ "$APPLY_MIGRATIONS" = "True" ]]; then
  echo "Applying migrations..."
  python /app/manage.py migrate --noinput
fi

if [[ "$CREATE_SUPERUSER" = "True" ]]; then
    python /app/manage.py createsuperuser --noinput || true
fi

if [[ "$DEV_SERVER" = "True" ]]; then
    python /app/manage.py runserver 0.0.0.0:8000
else
    daphne -b 0.0.0.0 -p 8000 project.asgi:application -t 60
fi