#!/bin/bash

set -ex

urlwait

python manage.py runserver 0.0.0.0:8000
