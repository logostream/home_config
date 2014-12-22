#!/bin/bash
# Synopsis:
#     :$ mirror_download.sh
#     enter password:
#     ^Z
#     :$ bg %1
#     :$ cat ~/log/mirror_sync.err # check error log
#     :$ tail -f ~/log/mirror_sync.log # check log
# Discription: sync whole repositories between mirrors
echo deprecated and disable by default
exit 1

SRC_PREFIX=stream@redland.cloudapp.net:$HOME
DEST=$HOME
rsync -e "ssh -p1109" -avvH --checksum --delete --exclude="cache/copy" --exclude="cache/github" "$SRC_PREFIX/data" "$SRC_PREFIX/cache" "$SRC_PREFIX/arch" "$DEST" > ~/log/mirror_sync.log 2> ~/log/mirror_sync.err
