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

echo "Getting ElasticSearch"
wget "https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-${ES_VERSION}.tar.gz"
tar xzvf elasticsearch-${ES_VERSION}.tar.gz

echo "Getting Redis"
wget "http://redis.googlecode.com/files/redis-${REDIS_VERSION}.tar.gz"
tar xzvf redis-${REDIS_VERSION}.tar.gz
pushd redis-${REDIS_VERSION}
  make
popd
