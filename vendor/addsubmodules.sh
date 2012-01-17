#!/bin/bash
for f in vendor/src/*; do
    pushd $f > /dev/null && REPO=$(git config remote.origin.url) && popd > /dev/null && git submodule add $REPO $f
done
