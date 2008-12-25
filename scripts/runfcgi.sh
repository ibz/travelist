#!/bin/bash

PROJDIR="/srv/fcgi/backpacked.it/backpackedit"
PIDFILE="$PROJDIR/tmp/mysite.pid"

cd $PROJDIR
if [ -f $PIDFILE ]; then
    kill `cat -- $PIDFILE`
    rm -f -- $PIDFILE
fi

exec /usr/bin/env - \
  PYTHONPATH="../python:.." \
  ./manage.py runfcgi pidfile=$PIDFILE host=127.0.0.1 port=3033
