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

LOCALEDIR="$1"
POTFILE="${LOCALEDIR}/templates/LC_MESSAGES/buddyup.pot"

if [ ! -e "${POTFILE}" ]; then
    echo "${POTFILE} does not exist. exiting."
    exit 1
fi

for lang in $(find $1 -type f -name "buddyup.po"); do
    echo -n "working on ${lang} "
    msgmerge --update ${lang} ${POTFILE}
done
