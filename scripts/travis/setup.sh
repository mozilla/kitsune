#!/bin/bash
# pwd is the git repo.
set -e

# None of this is needed for lint tests.
if [[ $TEST_SUITE == "lint" ]]; then
  exit 0
fi

echo "Making settings_local.py"
cat > kitsune/settings_local.py <<SETTINGS
from settings import *
ROOT_URLCONF = '%s.urls' % PROJECT_MODULE
LOG_LEVEL = logging.ERROR
DATABASES['default']['NAME'] = 'kitsune'
DATABASES['default']['HOST'] = 'localhost'
DATABASES['default']['USER'] = 'travis'
CELERY_ALWAYS_EAGER = True
CACHE_BACKEND = 'caching.backends.locmem://'
ES_INDEX_PREFIX = 'sumo'
ES_URLS = ['http://localhost:9200']
INSTALLED_APPS += ('django_qunit',)
SETTINGS

echo "Making redis.conf"
cat > redis-config.conf <<SETTINGS
daemonize yes
pidfile redis-state/redis-sumo-test.pid
port 6383
timeout 30
loglevel verbose
logfile stdout
databases 4
rdbcompression yes
dbfilename dump.rdb
dir redis-state/sumo-test/
maxmemory 107374182400
maxmemory-policy allkeys-lru
appendonly no
appendfsync everysec
activerehashing yes
SETTINGS

echo "Creating test database"
mysql -e 'create database kitsune'

echo "Updating product details"
python manage.py update_product_details

echo "Starting ElasticSearch"
pushd elasticsearch-0.90.10
  # This will daemonize
  ./bin/elasticsearch
popd

echo "Starting Redis Servers"
# This will daemonize
mkdir -p redis-state/sumo-test/
./redis-2.6.9/src/redis-server redis-config.conf

echo "Starting XVFB for Selenium tests."
/usr/bin/Xvfb :99 -ac -screen 0 1280x1024x16 >/dev/null 2>/dev/null &

echo "Doing static dance."
./manage.py nunjucks_precompile
./manage.py collectstatic --noinput > /dev/null
