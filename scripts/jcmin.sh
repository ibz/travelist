#!/bin/sh

function update_v {
    bzr diff $1 > /dev/null || head /dev/urandom | md5sum | head -c8 > $1.v
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
cat media/javascript/lib/google-maps/*.js media/javascript/google-maps-utils.js | scripts/lib/jsmin.py > media/javascript/c/google-maps-all.js
update_v media/javascript/c/google-maps-all.js

# notification JS
cat media/javascript/notification.js | scripts/lib/jsmin.py > media/javascript/c/notification.js
update_v media/javascript/c/notification.js

# trip JS
cat media/javascript/trip.js | scripts/lib/jsmin.py > media/javascript/c/trip.js
update_v media/javascript/c/trip.js

# the rest of JS
cat `for f in media/javascript/lib/jquery/*.js; do if [ ! -L $f ]; then echo $f; fi; done` media/javascript/utils.js | scripts/lib/jsmin.py > media/javascript/c/all.js
update_v media/javascript/c/all.js
