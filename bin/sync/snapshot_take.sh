#!/bin/bash
dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
src=$1
shift
dest=$1
shift
rsync_args=$@
backup=${dest}~

if [ ! -d "$src" ]; then
	echo "src path ($src) not exists"
	exit 1;
fi

if [[ $dest =~ ^.*/$ ]]; then
	echo "bad format for dest ($dest)";
	exit 3;
fi

if [ -d "$dest" ]; then
	if [ -d "$backup" ]; then
		echo "backup path ($backup) already exists"
		exit 2;
	fi
	cp -val "$dest" "$backup"
fi

$dir/rsync_cd.sh "$src" "$dest" --checksum $rsync_args
