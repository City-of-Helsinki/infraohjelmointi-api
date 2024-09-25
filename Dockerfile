FROM registry.access.redhat.com/ubi9/python-311:latest

WORKDIR /app

ENV STATIC_ROOT /srv/app/static
COPY . .

USER root

RUN TZ="Europe/Helsinki" && \
    yum -y update && \
    yum install -y nano \
    libffi-devel \
    gcc \
    python3 \
    python3-devel \
    python3-pip \
    postgresql \
    postgresql-devel \
    libpq-devel \
    unzip \
    bash \
    grep \
    cronie \
    libcap && \
    # Install pip packages (pandas and uwsgi) instead of using yum
    pip install pandas uwsgi && \
    # Ensure pip and python are accessible globally
    ln -s /usr/bin/pip3 /usr/local/bin/pip && \
    ln -s /usr/bin/python3 /usr/local/bin/python && \
    # Install Python project dependencies
    pip install --no-cache-dir -r requirements.txt && \
    # Collect static files using Django settings
    mkdir -p /srv/app/static && \
    DJANGO_SECRET_KEY="only-used-for-collectstatic" DATABASE_URL="sqlite:///" \
    python manage.py collectstatic --noinput && \
    chmod +x /app/sync-from-sap.sh

# Set user to nobody and group 0, to match OpenShift's UID/GID setup
USER nobody:0

ENTRYPOINT ["./docker-entrypoint.sh"]