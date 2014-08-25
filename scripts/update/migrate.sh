#!/bin/bash

# Run migrations for kitsune

source virtualenv/bin/activate
python schematic migrations
python manage.py migrate
