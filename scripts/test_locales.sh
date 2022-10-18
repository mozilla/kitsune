#!/bin/bash

# This creates a faux Pirate locale under xx and transforms all the
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
mkdir -p locale/xx/LC_MESSAGES

echo "copying pot files...."
for potfile in $(find locale/templates/LC_MESSAGES/ -name "*.pot")
do 
    stem=$(basename $potfile .pot)
    cp $potfile locale/xx/LC_MESSAGES/${stem}.po
done

echo "translate messages.po file...."
for pofile in $(find locale/xx/LC_MESSAGES/ -name "*.po")
do
    dennis-cmd translate --pipeline=html,pirate $pofile

    dir=$(dirname $pofile)
    stem=$(basename $pofile .po)
    msgfmt -o ${dir}/${stem}.mo $pofile
done
