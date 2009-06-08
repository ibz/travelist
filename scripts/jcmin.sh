#!/bin/sh

function update_v {
    bzr diff $1 > /dev/null || head /dev/urandom | md5sum | head -c8 > $1.v
}

function update_jsmin {
    bzr diff $1 > /dev/null || cat $1 | scripts/lib/jsmin.py > ${1%.*}.min.${1##*.}
}

# blueprint CSS
cp media/css/lib/blueprint/screen.css media/css/c/blueprint-screen.css
update_v media/css/c/blueprint-screen.css
cp media/css/lib/blueprint/ie.css media/css/c/blueprint-ie.css
update_v media/css/c/blueprint-ie.css

# the rest of CSS
cat media/css/lib/jquery/*.css media/css/main.css > media/css/c/all.css
update_v media/css/c/all.css

# google maps JS
cat media/javascript/lib/google-maps/*.js media/javascript/google-maps-utils.js > media/javascript/c/google-maps-all.js
update_jsmin media/javascript/c/google-maps-all.js
update_v media/javascript/c/google-maps-all.js

# notification JS
cat media/javascript/notification.js > media/javascript/c/notification.js
update_jsmin media/javascript/c/notification.js
update_v media/javascript/c/notification.js

# trip JS
cat media/javascript/trip.js > media/javascript/c/trip.js
update_jsmin media/javascript/c/trip.js
update_v media/javascript/c/trip.js

# the rest of JS
cat `for f in media/javascript/lib/jquery/*.js; do if [ ! -L $f ]; then echo $f; fi; done` media/javascript/utils.js > media/javascript/c/all.js
update_jsmin media/javascript/c/all.js
update_v media/javascript/c/all.js
