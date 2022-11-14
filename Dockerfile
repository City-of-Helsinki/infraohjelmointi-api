FROM alpine as base

WORKDIR /app

RUN TZ="Europe/Helsinki" apk add --update nano python3 py3-pip uwsgi postgresql-client netcat-openbsd gettext libpq-dev unzip bash && \
    ln -s /usr/bin/pip3 /usr/local/bin/pip && \
    ln -s /usr/bin/python3 /usr/local/bin/python

FROM base

ENV STATIC_ROOT /srv/app/static
COPY . .

RUN pip install --no-cache-dir -r requirements.txt && \
    mkdir -p /srv/app/static && \
    DJANGO_SECRET_KEY="only-used-for-collectstatic" DATABASE_URL="sqlite:///" \
    python manage.py collectstatic --noinput

# Openshift starts the container process with group zero and random ID
# we mimic that here with nobody and group zero
USER nobody:0

ENTRYPOINT ["./docker-entrypoint.sh"]