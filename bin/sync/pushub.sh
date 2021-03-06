#!/bin/bash
# Synopsis:
#     :$ mirror_sync.sh
#     enter password:
#     ^Z
#     :$ bg %1
#     :$ cat ~/log/mirror_sync.err # check error log
#     :$ tail -f ~/log/mirror_sync.log # check log
# Discription: sync whole repositories between mirrors

CELL=XXX
TMP=tmp
SERVER_ADDR=stream@foo
SERVER_DIR=pushub
CLIENT_DIR=$HOME/pushub
if [ ! -d $CLIENT_DIR ] ; then
	echo "Client directory $CLIENT_DIR doesn't exist"
	exit 1
fi
if [[ `ssh $SERVER_ADDR test -d $SERVER_DIR || echo not exist` ]] ; then
	echo "Server directory $SERVER_DIR doesn't exist"
	exit 1
fi

if [[ $1 == "-b" ]] ; then
	rsync -avvH --checksum --exclude "/$TMP" --delete "$SERVER_ADDR:$SERVER_DIR/" "$CLIENT_DIR"
else
	rsync -avvH --checksum --delete "$CLIENT_DIR/$TMP/" "$SERVER_ADDR:$SERVER_DIR/$CELL"
fi
