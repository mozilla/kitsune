#!/bin/bash
# pwd is the git repo.
set -e
uname -a
date

# This is ... lets not talk about how silly this is.
# IRC Notifications are started first, so that the notifications come promptly.

# In case this script bails early, define a no-op irc script.
echo "#!/bin/bash" > ./irc
chmod +x ./irc
function _die() {
  echo "No irc notifications" $@
  exit 0
}

# Don't notify for other repos.
if [ $TRAVIS_REPO_SLUG != "mozilla/kitsune" ]; then
  _die "Wrong repo."
fi

echo "Getting ii"
wget "http://dl.suckless.org/tools/ii-1.7.tar.gz"
tar xzvf ii-1.7.tar.gz
pushd ii-1.7
  make
popd

echo "Starting ii irc client for notifications."
irc_nick="sumo_travis$(date +%N | cut -c1-3)"
ii-1.7/ii -s irc.mozilla.org -i . -n $irc_nick &

for i in $(seq 0 30); do
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

./irc "Starting Travis build #${TRAVIS_BUILD_NUMBER} for ${TRAVIS_REPO_SLUG}/${TRAVIS_BRANCH} (${TRAVIS_COMMIT:0:8})"
./irc "https://travis-ci.org/mozilla/kitsune/builds/${TRAVIS_BUILD_ID}"

echo -----
head -n 5 < irc.mozilla.org/out
echo -----
