#!/bin/bash

exec celery -A kitsune beat
