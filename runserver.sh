#!/usr/bin/env bash

python3 socialdistribution/manage.py migrate
gunicorn --pythonpath socialdistribution/ socialdistribution.wsgi
