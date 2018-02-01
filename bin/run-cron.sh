#!/bin/bash

exec newrelic-admin run-program python manage.py runscript cron
