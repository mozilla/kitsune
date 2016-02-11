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

CMD="py.test"
CMD="${CMD} -r a"
CMD="${CMD} --verbose"
CMD="${CMD} --base-url http://localhost:8000"
CMD="${CMD} --html results.html"
CMD="${CMD} --driver Firefox"
CMD="${CMD} --variables scripts/travis/variables.json"
if [ -n "${MARK_EXPRESSION}" ]; then CMD="${CMD} -m \"${MARK_EXPRESSION}\""; fi
CMD="${CMD} tests/functional"

echo 'Running UI tests'
eval ${CMD}

echo 'Booyahkasha!'
