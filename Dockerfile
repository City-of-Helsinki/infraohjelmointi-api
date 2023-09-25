FROM alpine

WORKDIR /app

ENV STATIC_ROOT /srv/app/static
COPY . .

RUN TZ="Europe/Helsinki" apk add --update nano libffi-dev gcc \
    musl-dev python3-dev python3  py3-pip py3-pandas uwsgi \
    postgresql-client netcat-openbsd gettext libpq-dev unzip \
    bash grep busybox-suid dcron libcap && \
    ln -s /usr/bin/pip3 /usr/local/bin/pip && \
    ln -s /usr/bin/python3 /usr/local/bin/python && \
    # install python project modules
    pip install --no-cache-dir -r requirements.txt && \
    mkdir -p /srv/app/static && \
    DJANGO_SECRET_KEY="only-used-for-collectstatic" DATABASE_URL="sqlite:///" \
    python manage.py collectstatic --noinput && \
    chmod +x /app/sync-from-sap.sh

# Openshift starts the container process with group zero and random ID
# we mimic that here with nobody and group zero
USER nobody:0

ENTRYPOINT ["./docker-entrypoint.sh"]