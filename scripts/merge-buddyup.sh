#!/bin/bash

# syntax:
# merge-buddyup.sh locale-dir/

function usage() {
    echo "syntax:"
    echo "merge-buddyup.sh locale-dir/"
    exit 1
}

# check if file and dir are there
if [[ ($# -ne 1) || (! -d "$1") ]]; then
    usage
fi

POTFILE=`find $1 -type f -name "buddyup.pot"`

for lang in `find $1 -type f -name "buddyup.po"`; do
    echo -n "working on ${lang} "
    msgmerge --update ${lang} ${POTFILE}
done
