#!/bin/bash
# This script should run from inside Hudson

cd $WORKSPACE
VENV=$WORKSPACE/venv

echo "Starting build..."

if [ -z $1 ]; then
    echo "Warning: You should provide a unique name for this job to prevent database collisions."
    echo "Usage: ./build.sh <name>"
    echo "Continuing, but don't say you weren't warned."
    BUILD_NAME='default'
else
    BUILD_NAME=$1
fi

if [ -z $2 ]; then
    echo "Warning: You should provide a unique Sphinx port for this build."
    SPHINX_PORT=3381
else
    SPHINX_PORT=$2
fi


# Clean up after last time.
find . -name '*.pyc' -delete;

# Using a virtualenv for python26 and compiled requirements.
if [ ! -d "$VENV/bin" ]; then
    echo "No virtualenv found; making one..."
    virtualenv --no-site-packages $VENV
fi
source $VENV/bin/activate
pip install -r requirements/tests-compiled.txt

# Fix any mistakes with private repos.
git submodule sync

# Using a vendor library for the rest.
git submodule update --init --recursive

python manage.py update_product_details

cat > settings_local.py <<SETTINGS
from settings import *
ROOT_URLCONF = '%s.urls' % ROOT_PACKAGE
LOG_LEVEL = logging.ERROR
DATABASES['default']['NAME'] = 'kitsune_$BUILD_NAME'
DATABASES['default']['HOST'] = 'localhost'
DATABASES['default']['USER'] = 'hudson'
DATABASES['default']['TEST_NAME'] = 'test_kitsune_$BUILD_NAME'
DATABASES['default']['TEST_CHARSET'] = 'utf8'
DATABASES['default']['TEST_COLLATION'] = 'utf8_general_ci'
TEST_SPHINX_PORT = $SPHINX_PORT
TEST_SPHINXQL_PORT = TEST_SPHINX_PORT + 1
CELERY_ALWAYS_EAGER = True
CACHE_BACKEND = 'caching.backends.locmem://'
SETTINGS

echo "Starting tests..." `date`
export FORCE_DB=1
if [ -z $COVERAGE ]; then
    python manage.py test --noinput --logging-clear-handlers --with-xunit
else
    coverage run manage.py test --noinput --logging-clear-handlers --with-xunit
    coverage xml $(find apps lib -name '*.py')
fi

echo 'Booyahkasha!'
