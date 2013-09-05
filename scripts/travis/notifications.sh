#!/bin/bash
# pwd is the git repo.
set -e
uname -a
date

# This is ... lets not talk about how silly this is.
# IRC Notifications are started first, so that the notifications come promptly.
#
# This uses ii, a odd irc client that maps channels and servers to the
# filesystem. See http://tools.suckless.org/ii/ for more details.
#
# This uses a bunch of Travis environment variables, which are documented at
# http://about.travis-ci.org/docs/user/ci-environment/

# In case this script bails early, define a no-op irc script.
echo "#!/bin/bash" > ./irc
chmod +x ./irc
function _die() {
  echo "No irc notifications" $@
  [ -f irc.mozilla.org/out ] && cat irc.mozilla.org/out
  exit 0
}

# Don't notify for other repos.
if [ $TRAVIS_REPO_SLUG != "mozilla/kitsune" ]; then
  _die "Wrong repo."
fi

echo "Installing ii"
tar xzvf scripts/travis/ii-1.7.tar.gz
pushd ii-1.7
  make
popd

echo "Starting ii irc client for notifications."
irc_nick="sumo_travis$(date +%N | cut -c1-3)"
ii-1.7/ii -s irc.mozilla.org -i . -n $irc_nick &

for i in $(seq 0 30); do
  echo -n "$i "
  if [ $i -ge 30 ]; then
    _die "Timeout."
  fi
  if [ ! -p irc.mozilla.org/in ]; then
    sleep 1
    continue
  fi
  if grep "End of /MOTD" irc.mozilla.org/out; then
    break
  fi
  if grep "Nickname is already in use."; then
    # Oh well.
    _die "Nick already in use."
  fi
  sleep 1
done

echo -ne "IRC: "
echo "/j #sumodev" | tee irc.mozilla.org/in

while [ ! -p irc.mozilla.org/#sumodev/in ]; do
  sleep 0.1
done

echo 'echo -ne "IRC: "' >> ./irc
echo 'echo "$@" | tee irc.mozilla.org/#sumodev/in' >> ./irc

if [ $TRAVIS_PULL_REQUEST == 'false' ]; then
  ./irc "Travis #${TRAVIS_BUILD_NUMBER} starting for ${TRAVIS_REPO_SLUG} branch ${TRAVIS_BRANCH} (${TRAVIS_COMMIT:0:8})"
else
  ./irc "Travis #${TRAVIS_BUILD_NUMBER} starting for ${TRAVIS_REPO_SLUG} pull #${TRAVIS_PULL_REQUEST}"
fi
./irc "https://travis-ci.org/mozilla/kitsune/builds/${TRAVIS_BUILD_ID}"

echo -----
head -n 5 < irc.mozilla.org/out
echo -----
