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

# SSE responses never finish on their own, so shutdowns and reloads would wait
# for every open tab; after 5 s uvicorn closes them and browsers reconnect.
if [[ "$DEV_SERVER" = "True" ]]; then
    # uvicorn, not runserver: runserver is WSGI and can't stream /events/ (SSE).
    uvicorn project.asgi:application --host 0.0.0.0 --port 8000 --reload --timeout-graceful-shutdown 5 \
        --http h11 --h11-max-incomplete-event-size "${H11_MAX_INCOMPLETE_EVENT_SIZE:-65536}"
else
    # h11 rejects headers >16KB by default; helsinki-tunnistus tokens of users with many AD groups exceed that.
    uvicorn project.asgi:application --host 0.0.0.0 --port 8000 --workers $WORKERS_AMOUNT_FOR_UVICORN --timeout-graceful-shutdown 5 \
        --http h11 --h11-max-incomplete-event-size "${H11_MAX_INCOMPLETE_EVENT_SIZE:-65536}"
fi