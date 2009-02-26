#!/bin/sh

# blueprint
cp media/css/lib/blueprint/screen.css media/css/c/blueprint-screen.css
head /dev/urandom | md5sum | head -c8 > media/css/c/blueprint-screen.css.v

cp media/css/lib/blueprint/ie.css media/css/c/blueprint-ie.css
head /dev/urandom | md5sum | head -c8 > media/css/c/blueprint-ie.css.v

# the rest
cat media/css/lib/jquery/*.css media/css/main.css > media/css/c/all.css
head /dev/urandom | md5sum | head -c8 > media/css/c/all.css.v
