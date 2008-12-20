#!/bin/sh

cat media/css/lib/jquery/*.css media/css/main.css > media/css/c/all.css
cp media/css/lib/blueprint/screen.css media/css/c/blueprint-screen.css
cp media/css/lib/blueprint/ie.css media/css/c/blueprint-ie.css

gzip --to-stdout media/css/c/all.css > media/css/c/all.cgz
gzip --to-stdout media/css/c/blueprint-screen.css > media/css/c/blueprint-screen.cgz
gzip --to-stdout media/css/c/blueprint-ie.css > media/css/c/blueprint-ie.cgz
