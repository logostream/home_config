#!/bin/bash
# Synopsis:
#     :$ mirror_upload.sh
#     enter password:
#     ^Z
#     :$ bg %1
#     :$ cat ~/log/mirror_sync.err # check error log
#     :$ tail -f ~/log/mirror_sync.log # check log
# Discription: sync whole repositories between mirrors (only arch/ by now)

SRC=/archived/stream/ # content only
DEST=stream@redland.cloudapp.net:$HOME/arch
rsync -e "ssh -p1109" -avvH --checksum --delete \
		  "$SRC" "$DEST" 2> ~/log/mirror_sync.err | tee ~/log/mirror_sync.log
