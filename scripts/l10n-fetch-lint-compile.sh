#!/bin/bash

# Run this from the project root--not from this directory!

git clone https://github.com/mozilla-l10n/sumo-l10n.git locale
cd locale

postatus_file=../kitsune/sumo/static/postatus.txt
head_hash=$(git log -n1 --format=%H)
echo "po status for commit ${head_hash}:" > $postatus_file
echo -e "(if nothing appears below, no errors were detected)\\n" >> $postatus_file

function lintpo() {
    commit=$1
    pofile=$2

    log=$(../scripts/dennis_shim.py lint --errorsonly "${pofile}")
    if [ $? -eq 0 ]
    then
        compilemo $pofile
        return 0
    fi

    if [ $commit = "HEAD" ]
    then
        echo "$log" >> $postatus_file
        echo -e "\\n" >> $postatus_file
    fi

    # find the next most recent commit the file was modified in
    commit=$(git log -n1 --format=%H ${commit}~1 -- $pofile)
    echo "lint returned an error, trying $commit"
    # checkout the file from that commit
    git checkout $commit $pofile
    # try linting again
    lintpo $commit $pofile
}

function compilemo() {
    dir=`dirname $1`
    stem=`basename $1 .po`

    msgfmt -o "${dir}/${stem}.mo" "$1"
}

for pofile in `find ./ -name "*.po"`
do
    echo "Linting and compiling ${pofile}..."
    lintpo HEAD $pofile
done
