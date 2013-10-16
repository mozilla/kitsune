#!/bin/bash

# Run this from the project root--not from this directory!

function compilemo() {
    dir=`dirname $1`
    stem=`basename $1 .po`

    echo "Compiling $1..."
    msgfmt -o "${dir}/${stem}.mo" "$1"
}

NO_MO_FILES=();
GOOD_FILES=();
BAD_FILES=();

for pofile in `find locale/ -name "*.po"`
do
    dir=`dirname $pofile`
    stem=`basename $pofile .po`

    # If no .mo file exists, we compile it. If it does exist, then we
    # lint the .po file and only compile to .mo if it's error-free.
    if [ ! -e "${dir}/${stem}.mo" ]
    then
        compilemo $pofile
        NO_MO_FILES+=("${pofile}")

    else
        ./manage.py lint --errorsonly "${pofile}"
        if [ $? -ne 0 ]
        then
            BAD_FILES+=("${pofile}")

        else
            compilemo $pofile
            GOOD_FILES+=("${pofile}")
        fi
    fi
done

for pofile in ${NO_MO_FILES[@]}
do
    echo "NO MO FILE: ${pofile}"
done

for pofile in ${BAD_FILES[@]}
do
    echo "BUSTED: ${pofile}"
done

for pofile in ${GOOD_FILES[@]}
do
    echo "COMPILED: ${pofile}"
done
