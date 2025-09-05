#!/bin/bash

set -ex

# Install Node dependencies, run the webpack build, and pre-render the svelte templates.
npm run development && npm run webpack:build && npm run webpack:build:pre-render