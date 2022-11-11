FROM alpine as base

WORKDIR /app

RUN TZ="Europe/Helsinki" apk add --update nano python3 py3-pip uwsgi postgresql-client netcat-openbsd gettext libpq-dev unzip && \
    ln -s /usr/bin/pip3 /usr/local/bin/pip && \
    ln -s /usr/bin/python3 /usr/local/bin/python

FROM base

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Openshift starts the container process with group zero and random ID
# we mimic that here with nobody and group zero
USER nobody:0

ENTRYPOINT ["gunicorn"]