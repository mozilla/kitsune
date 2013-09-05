#!/bin/bash
# pwd is the git repo.
set -e
uname -a
date

echo "Fixing path issues"
sudo ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so ~/virtualenv/python2.6/lib/
sudo ln -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so ~/virtualenv/python2.6/lib/
sudo ln -s /usr/lib/`uname -i`-linux-gnu/libz.so ~/virtualenv/python2.6/lib/

echo "Install Python dependencies"
pip install -r requirements/compiled.txt

echo "Installing Node.js dependencies"
npm install

echo "Extracting ElasticSearch"
tar xzvf elasticsearch-*.tar.gz

echo "Building Redis"
tar xzvf vendor/tarballs/redis-*.tar.gz
pushd redis-${REDIS_VERSION}
  make
popd
