#!/bin/bash
# pwd is the git repo.
set -e

echo "Fix path issues"
sudo ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so ~/virtualenv/python2.6/lib/
sudo ln -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so ~/virtualenv/python2.6/lib/
sudo ln -s /usr/lib/`uname -i`-linux-gnu/libz.so ~/virtualenv/python2.6/lib/

echo "Install Python dependencies"
pip install --allow-external PIL --allow-unverified PIL -r requirements/compiled.txt > /dev/null
pip install nosenicedots > /dev/null
pip freeze
echo

echo "Installing Node.js dependencies"
npm install > /dev/null 2> /dev/null
npm list
echo

echo "Installing ElasticSearch"
tar xzvf vendor/tarballs/elasticsearch-0.20.5.tar.gz > /dev/null

echo "Installing Redis"
tar xzvf vendor/tarballs/redis-2.4.11.tar.gz > /dev/null
pushd redis-2.4.11
  make > /dev/null 2> /dev/null
popd
