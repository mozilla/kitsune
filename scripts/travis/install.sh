#!/bin/bash
# pwd is the git repo.
set -e

echo "Fix path issues"
ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so ~/virtualenv/python2.6/lib/
ln -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so ~/virtualenv/python2.6/lib/
ln -s /usr/lib/`uname -i`-linux-gnu/libz.so ~/virtualenv/python2.6/lib/

echo "Install Python dependencies"
python scripts/peep.py install \
  -r requirements/dev.txt \
  --no-use-wheel

# Optimization: None of the rest is needed for lint tests.
if [[ $TEST_SUITE == "lint" ]]; then
  exit 0
fi

python scripts/peep.py install \
  -r "requirements/default.txt" \
  --no-use-wheel
# Print the installed packages for the world to see.
pip freeze
echo


echo "Installing Node.js dependencies"
npm install > /dev/null 2> /dev/null
npm list
echo


echo "Intalling front end dependencies"
./node_modules/.bin/bower install > /dev/null 2> /dev/null
./node_modules/.bin/bower list -o
echo


echo "Installing ElasticSearch"
tar xzvf vendor/tarballs/elasticsearch-0.90.10.tar.gz > /dev/null

echo "Installing Redis"
tar xzvf vendor/tarballs/redis-2.6.9.tar.gz > /dev/null
pushd redis-2.6.9
  make > /dev/null 2> /dev/null
popd
