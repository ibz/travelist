#!/bin/sh

cat media/css/lib/jquery/*.css media/css/main.css > media/css/c/all.css
cat media/javascript/lib/jquery/*.js media/javascript/utils.js | scripts/lib/jsmin.py > media/javascript/c/all.js
