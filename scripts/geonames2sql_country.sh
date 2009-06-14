#!/bin/sh

if [ -z $1 ]; then
    echo "Need input file."
    exit 1
fi

if [ -z $2 ]; then
    echo "Need output file."
    exit 1
fi

cat $1 | grep "^[A-Z]" | awk -F "\t" 'BEGIN { print "BEGIN;"; } END { print "COMMIT;"; } { printf("INSERT INTO backpacked_country(code, name) VALUES('"'"'%s'"'"', '"'"'%s'"'"');\n", $1, $5); }' > $2
