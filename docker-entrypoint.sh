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
    uvicorn project.asgi:application --host 0.0.0.0 --port 8000
fi