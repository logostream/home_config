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

$dir/rsync_cd.sh "$src" "$dest" $rsync_args -n
