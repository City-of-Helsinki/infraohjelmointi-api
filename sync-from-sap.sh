#!/bin/sh

set -e

# needed for crontab
cd /app
# full path for python needed fron crontab
/usr/local/bin/python manage.py sapsyncrhonizer
