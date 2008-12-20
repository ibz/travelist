#!/bin/sh

cat media/css/lib/jquery/*.css media/css/main.css > media/css/c/all.css
cat media/javascript/lib/jquery/*.js media/javascript/utils.js | scripts/lib/jsmin.py > media/javascript/c/all.js

gzip --to-stdout media/javascript/c/all.js > media/javascript/c/all.jgz
gzip --to-stdout media/css/c/all.css > media/css/c/all.cgz
