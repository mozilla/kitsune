#!/bin/bash
# pwd is the git repo.
set -e
date

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

echo "Creating test database"
mysql -e 'create database kitsune'

echo "Updating product details"
python manage.py update_product_details

echo "Starting ElasticSearch"
pushd elasticsearch-0.20.5
  # This will daemonize
  ./bin/elasticsearch
popd

echo "Starting Redis Servers"
# This will daemonize
sudo mkdir -p /var/redis/sumo-test/
sudo chown `whoami` -R /var/redis/
./redis-2.4.11/src/redis-server configs/redis/redis-test.conf

echo "Starting XVFB for Selenium tests."
/usr/bin/Xvfb :99 -ac -screen 0 1280x1024x16 >/dev/null &

echo "Doing static dance."
./manage.py collectstatic --noinput
./manage.py compress_assets
