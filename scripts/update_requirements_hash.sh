#!/bin/bash

# Run from the home of the project, not from the scripts folder.

trap "exit" INT;

cd requirements;

function peepin_file {
    OUTPUT_FILE=$1;
    INPUT_FILE="$OUTPUT_FILE.bak";
    cp $OUTPUT_FILE $INPUT_FILE;

    echo "=== $OUTPUT_FILE ==="
    while read line; do
        [[ -z $line ]] && continue;
        [[ $line == 'http:'* ]] && continue;
        [[ $line == 'https:'* ]] && continue;
        [[ $line == '#'* ]] && continue;
        echo $line;
        peepin $line $OUTPUT_FILE;
    done < $INPUT_FILE;
}

for file in *.txt; do
    peepin_file $file;
done;

