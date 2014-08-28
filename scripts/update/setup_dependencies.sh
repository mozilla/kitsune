#!/bin/bash

# This creates a virtualenv and installs our requirements into it.
# CWD should be the project folder, i.e. kitsune/.

if [ ! -d "virtualenv" ]; then
    virtualenv --no-site-packages --verbose virtualenv
fi
source virtualenv/bin/activate
python scripts/peep.py install -r requirements/requirements_src.txt
python scripts/peep.py install -r requirements/requirements_packages.txt

# Make sure all files in virtualenv can be rsynced.
virtualenv --system-site-packages --relocatable virtualenv
