#!/bin/bash
# pwd is the git repo.
set -e

# For XVFB Selenium tests.
echo "Starting Browser for Smoke Tests"
export DISPLAY=:99.0

echo 'Starting a server'
./manage.py runserver &
sleep 3

echo 'Running Smoke tests'
source selenium/bin/activate
cd smoketests
xvfb-run --server-args="-screen 0, 1280x1024x16" py.test --driver=firefox --baseurl=http://localhost:8000 tests
echo 'Booyahkasha!'
