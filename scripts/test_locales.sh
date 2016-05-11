#!/bin/bash

# This creates a faux Pirate locale under xx_testing and transforms all the
# strings such that every resulting string has four properties:
#
# 1. it's longer than the English equivalent (tests layout issues)
# 2. it's different than the English equivalent (tests missing gettext calls)
# 3, every string ends up with a non-ascii character (tests unicode)
# 4. looks close enough to the English equivalent that you can quickly
#    figure out what's wrong
#
# Run this from the project root directory like this:
#
# $ scripts/test_locales.sh

echo "create required directories..."
mkdir -p locale/templates/LC_MESSAGES

echo "extract and merge...."
./manage.py extract
./manage.py merge

echo "creating dir...."
mkdir -p locale/xx_testing/LC_MESSAGES

echo "copying *.pot files...."
cp locale/templates/LC_MESSAGES/*.pot locale/xx_testing/LC_MESSAGES/
for pot_file in locale/xx_testing/LC_MESSAGES/*.pot;
    do mv $pot_file locale/xx_testing/LC_MESSAGES/`basename $pot_file .pot`.po;
done

echo "translate *.po files...."
./manage.py translate --pipeline=html,pirate locale/xx_testing/LC_MESSAGES/*.po
./scripts/compile-mo.sh locale/xx_testing/
