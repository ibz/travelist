#!/bin/sh

if [ -z $1 ]; then
    echo "Need input file."
    exit 1
fi

if [ -z $2 ]; then
    echo "Need output file."
    exit 1
fi

cat $1 | sed -e "s/'/''/g" | awk -F "\t" 'BEGIN { print "BEGIN;"; } END { print "COMMIT;"; }{ print "INSERT INTO backpacked_place(name, coords) VALUES(trim('"'"'", $2, "'"'"'), GeometryFromText('"'"'POINT(", $5, $6, ")'"'"', 4326));";}' > $2

