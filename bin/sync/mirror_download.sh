#!/bin/bash
# Synopsis:
#     :$ mirror_download.sh
#     enter password:
#     ^Z
#     :$ bg %1
#     :$ cat ~/log/mirror_sync.err # check error log
#     :$ tail -f ~/log/mirror_sync.log # check log
# Discription: sync whole repositories between mirrors

echo "This gonna to wipeout entire local data. Double check before comment out following line"
exit 1

SRC=stream@redland.cloudapp.net:$HOME/arch
DEST=/archived/stream
rsync -e "ssh -p1109" -avvH --checksum --delete "$SRC" "$DEST" 2>&1 | tee ~/log/mirror_sync.log
