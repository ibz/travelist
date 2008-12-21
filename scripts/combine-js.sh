#!/bin/sh

cat media/javascript/lib/jquery/*.js media/javascript/utils.js | scripts/lib/jsmin.py > media/javascript/c/all.js
head /dev/urandom | md5sum | head -c8 > media/javascript/c/all.js.v
