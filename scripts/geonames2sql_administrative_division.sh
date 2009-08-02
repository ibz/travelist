#!/bin/sh

if [ -z $1 ]; then
    echo "Need input file."
    exit 1
fi

if [ -z $2 ]; then
    echo "Need output file."
    exit 1
fi

cat $1 | sed -e "s/'/''/g" | awk -F "\t" 'BEGIN { print "BEGIN;"; } END { print "COMMIT;"; } { printf("INSERT INTO travelist_administrativedivision(code, name, country_id) VALUES('"'"'%s'"'"', '"'"'%s'"'"', (SELECT id FROM travelist_country WHERE code = '"'"'%s'"'"'));\n", substr($1, 4), $2, substr($1, 1, 2)); }' > $2
