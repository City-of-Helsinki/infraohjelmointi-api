FROM registry.access.redhat.com/ubi9/python-311:latest

WORKDIR /app

ENV STATIC_ROOT /srv/app/static
COPY . .

USER root

RUN TZ="Europe/Helsinki" \
    yum -y update && \
    yum install -y gcc libffi-devel python3-devel libpq-devel unzip bash gettext cronie && \
    yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-aarch64/pgdg-redhat-repo-latest.noarch.rpm && \
    yum -y install postgresql13 && \
    yum clean all && \
    rm -rf /var/cache/yum && \
    pip install --no-cache-dir -r requirements.txt && \
    mkdir -p /srv/app/static && \
    chmod +x /app/sync-from-sap.sh && \
    python manage.py collectstatic --noinput && \
    chown -R nobody:nobody /srv/app/static

USER nobody:0

ENTRYPOINT ["./docker-entrypoint.sh"]