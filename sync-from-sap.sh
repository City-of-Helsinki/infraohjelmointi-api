#!/bin/sh

set -e

# needed for crontab
cd /app
# full path for python needed fron crontab
/opt/app-root/bin/python manage.py sapsynchronizer
