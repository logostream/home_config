#!/bin/bash
dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
src=$1
shift
dest=$1
shift
rsync_args=$@

if [ ! -d "$src" ]; then
	echo "src path ($src) not exists"
	exit 1;
fi

if [ ! -d "$dest" ]; then
	echo "dest path ($dest) not exists"
	exit 2;
fi

$dir/rsync_cd.sh "$src" "$dest" --checksum $rsync_args
