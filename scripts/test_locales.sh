#!/bin/bash

# This creates a faux Pirate locale under xx and transforms
# all the strings such that every resulting string has four
# properties:
#
# 1. it's longer than the English equivalent (tests layout issues)
# 2. it's different than the English equivalent (tests missing
# gettext calls) 3, every string ends up with a non-ascii character
# (tests unicode) 4. looks close enough to the English equivalent
# that you can quickly figure out what's wrong
#
# Run this from the project root directory like this:
#
# $ scripts/test_locales.sh

echo "Create required directories..."
mkdir -p locale/templates/LC_MESSAGES

echo "Extract and merge...."
./manage.py extract > /dev/null
./manage.py merge > /dev/null &2>/dev/null

echo "Creating xx_testing locale dir...."
mkdir -p locale/xx_testing/LC_MESSAGES

for template in locale/templates/LC_MESSAGES/*.pot; do
    name=$(basename $template .pot)
    pofile="locale/xx_testing/LC_MESSAGE/${name}.po"
    echo "Copying $name.pot to $name.po..."
    cp $template $pofile
    echo "Translating $name.po..."
    ./manage.py translate --pipeline=html,pirate $pofile > /dev/null
done

echo "Compile .mo files"
locale/compile-mo.sh locale/xx_testing/ > /dev/null
