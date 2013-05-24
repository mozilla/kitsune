# This script should be called from within Hudson


cd $WORKSPACE
VENV=$WORKSPACE/venv
LOG=$WORKSPACE/jstests-runserver.log

echo "Starting build on executor $EXECUTOR_NUMBER..." `date`

if [ -z $1 ]; then
    echo "Warning: You should provide a unique name for this job to prevent database collisions."
    echo "Usage: $0 <name>"
    echo "Continuing, but don't say you weren't warned."
    BUILD_NAME='default'
else
    BUILD_NAME=$1
fi

echo "Setup..." `date`

# Make sure there's no old pyc files around.
find . -name '*.pyc' | xargs rm

# Using a virtualenv for python26 and compiled requirements.
if [ ! -d "$VENV/bin" ]; then
  echo "No virtualenv found.  Making one..."
  virtualenv $VENV
fi
source $VENV/bin/activate
pip install -q -r requirements/tests-compiled.txt

# Fix any mistakes with private repos.
git submodule sync

# Using a vendor library for the rest.
git submodule update --init --recursive

python manage.py update_product_details

cat > kitsune/settings_local.py <<SETTINGS
from settings import *
ROOT_URLCONF = '%s.urls' % ROOT_PACKAGE
LOG_LEVEL = logging.ERROR
DATABASES['default']['NAME'] = 'test_kitsune_$BUILD_NAME'
DATABASES['default']['HOST'] = 'localhost'
DATABASES['default']['USER'] = 'hudson'
DATABASES['default']['TEST_NAME'] = 'test_kitsune_$BUILD_NAME'
DATABASES['default']['TEST_CHARSET'] = 'utf8'
DATABASES['default']['TEST_COLLATION'] = 'utf8_general_ci'
CACHE_BACKEND = 'caching.backends.locmem://'
CELERY_ALWAYS_EAGER = True
ES_INDEX_PREFIX = 'sumo_$BUILD_NAME'

# Activate Qunit:
INSTALLED_APPS += (
    'django_qunit',
)

SETTINGS

echo "CREATE DATABASE test_kitsune_$BUILD_NAME" | mysql

# All DB tables need to exist so that runserver can start up.
python manage.py syncdb --noinput

echo "Starting JS tests..." `date`

rm $LOG
# NOTE: the host value here needs to match the 'kitsune' suite in jstestnet
cd scripts
python run_jstests.py -v --with-xunit --with-django-serv --django-host $DJANGO_HOST --django-port $DJANGO_PORT --django-log $LOG --with-jstests --jstests-server http://jstestnet.farmdev.com/ --jstests-suite sumo --jstests-token $JSTESTS_TOKEN --jstests-url http://$DJANGO_HOST:$DJANGO_PORT/en-US/qunit --jstests-browsers firefox --debug nose.plugins.jstests

echo 'shazam!'
