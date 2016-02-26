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
DATABASES['default']['CONN_MAX_AGE'] = 600
CELERY_ALWAYS_EAGER = True
ES_INDEX_PREFIX = 'sumo'
ES_URLS = ['http://localhost:9200']
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

echo "Setting mysql params to get around 'mysql has gone away' errors"
mysql -e "SET GLOBAL sql_mode = 'NO_ENGINE_SUBSTITUTION,STRICT_TRANS_TABLES'"
mysql -e "SET GLOBAL wait_timeout = 36000;"
mysql -e "SHOW VARIABLES LIKE 'wait_timeout';"
mysql -e "SET GLOBAL max_allowed_packet = 134209536;"
mysql -e "SHOW VARIABLES LIKE 'max_allowed_packet';"

echo "Creating test database"
mysql -e 'create database kitsune'

echo "Updating product details"
python manage.py update_product_details

echo "Starting ElasticSearch"
ELASTICSEARCH_VERSION=${ELASTICSEARCH_VERSION:-1.2.4}
pushd elasticsearch-${ELASTICSEARCH_VERSION}
  # New version of ES are foreground by default, old ones are backgrounded by default
  if [[ $ELASTICSEARCH_VERSION == '1.2.4' ]]; then
    # -d to daemonize
    ./bin/elasticsearch -d
  else
    # This will daemonize
    ./bin/elasticsearch
  fi
popd

echo "Starting Redis Servers"
# This will daemonize
mkdir -p redis-state/sumo-test/
./redis-2.6.9/src/redis-server redis-config.conf

echo "Running migrations"
./manage.py migrate --list
./manage.py migrate

echo "Doing static dance."
./manage.py nunjucks_precompile
./manage.py compilejsi18n
./manage.py collectstatic --noinput > /dev/null
