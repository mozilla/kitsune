#!/bin/bash
# pwd is the git repo.
set -e
echo "Downgrading default pip"
pip install -U "pip<8"

echo "Install Python dependencies"
./peep.sh install -r requirements/dev.txt
./peep.sh install -r requirements/default.txt
echo

# Installing dependencies for UI tests
if [[ $TEST_SUITE == "ui" ]]; then
  pip install tox
fi

# Optimization: None of the rest is needed for lint tests.
if [[ $TEST_SUITE == "lint" ]]; then
  exit 0
fi

echo "Installing Node.js dependencies"
npm install
echo

echo "Installing front end dependencies"
./node_modules/.bin/bower install
echo


echo "Installing ElasticSearch"
curl -O https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/deb/elasticsearch/2.3.0/elasticsearch-2.3.0.deb && sudo dpkg -i --force-confnew elasticsearch-2.3.0.deb && sudo service elasticsearch restart

echo "Installing Redis"
tar xzvf vendor/tarballs/redis-2.6.9.tar.gz > /dev/null
pushd redis-2.6.9
  make > /dev/null 2> /dev/null
popd
