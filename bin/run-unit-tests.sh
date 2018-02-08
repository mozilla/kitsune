#!/bin/bash

./manage.py test --noinput --nologcapture -a '!search_tests' --with-nicedots
