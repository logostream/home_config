#!/bin/bash
# Synopsis:
#     :$ mirror_upload.sh
#     enter password:
#     ^Z
#     :$ bg %1
#     :$ cat ~/log/mirror_sync.err # check error log
#     :$ tail -f ~/log/mirror_sync.log # check log
# Discription: sync whole repositories between mirrors

SRC_PREFIX=$HOME
DEST=stream@redland.cloudapp.net:$HOME
rsync -e "ssh -p1109" -avvH --checksum --delete \
		  "$SRC_PREFIX/cache" \
		  "$SRC_PREFIX/data" \
		  "$SRC_PREFIX/pushub" \
		  "$SRC_PREFIX/github" \
		  "$SRC_PREFIX/arch" \
		  "$DEST" 2> ~/log/mirror_sync.err | tee ~/log/mirror_sync.log
