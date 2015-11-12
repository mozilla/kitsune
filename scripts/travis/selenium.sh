#!/bin/bash
# pwd is the git repo.
set -e

# For XVFB Selenium tests.
echo "Starting Browser for Selenium Tests"
export DISPLAY=:99.0

echo 'Starting a server'
./manage.py runserver &
sleep 3

echo 'Running Selenium tests'
source smoketests/bin/activate
cd smoketests
xvfb-run py.test --driver=firefox --baseurl=http://localhost:8000 tests
echo 'Booyahkasha!'
