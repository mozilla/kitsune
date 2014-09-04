#!/bin/bash

# This creates a virtualenv and installs our requirements into it.
# CWD should be the project folder, i.e. kitsune/.

set -e -u

virtualenv --system-site-packages virtualenv

source virtualenv/bin/activate
python scripts/peep.py install -r requirements/requirements_src.txt
python scripts/peep.py install -r requirements/requirements_packages.txt

# Fix path issues for when we rsync..
virtualenv --relocatable virtualenv
