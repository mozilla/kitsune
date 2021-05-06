#!/bin/bash
# pwd is the git repo.
set -ex

echo "Starting XVFB for UI tests"
export DISPLAY=:99.0
/sbin/start-stop-daemon --start --quiet --pidfile /tmp/custom_xvfb_99.pid --make-pidfile --background --exec /usr/bin/Xvfb -- :99 -ac -screen 0 1280x1024x16

echo 'Starting a server'
./manage.py shell < ./scripts/create_user_and_superuser.py
./manage.py generatedata
./manage.py runserver &
sleep 3

PYTEST_ADDOPTS="--base-url=http://localhost:8000"
PYTEST_ADDOPTS="${PYTEST_ADDOPTS} --variables=scripts/travis/variables.json"
if [ -n "${MARK_EXPRESSION}" ]; then PYTEST_ADDOPTS="${PYTEST_ADDOPTS} -m=\"${MARK_EXPRESSION}\""; fi

echo 'Running UI tests'
tox

echo 'Booyahkasha!'
