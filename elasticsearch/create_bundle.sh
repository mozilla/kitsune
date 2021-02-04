#!/bin/bash

zip -r es_bundle_$(date +%s)_$(git rev-parse --short HEAD).zip dictionaries
