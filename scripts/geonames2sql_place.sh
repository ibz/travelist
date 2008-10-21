#!/bin/sh

if [ -z $1 ]; then
    echo "Need input file."
    exit 1
fi

if [ -z $2 ]; then
    echo "Need output file."
    exit 1
fi

cat $1 | sed -e "s/'/''/g" | awk -F "\t" 'BEGIN { print "BEGIN;"; } END { print "COMMIT;"; } { printf("INSERT INTO backpacked_place(code, name, name_ascii, country_id, administrative_division_id, coords) VALUES(%s, '"'"'%s'"'"', '"'"'%s'"'"', (SELECT id FROM backpacked_country WHERE code = '"'"'%s'"'"'), (SELECT id FROM backpacked_administrativedivision WHERE country_id = (SELECT id FROM backpacked_country WHERE code = '"'"'%s'"'"') AND code = '"'"'%s'"'"'), GeometryFromText('"'"'POINT(%s %s)'"'"', 4326));\n", $1, $2, $3, $9, $9, $11, $5, $6); }' > $2

