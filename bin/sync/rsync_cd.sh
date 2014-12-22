#!/bin/bash
src=$1
shift
dest=$1
shift
rsync_args=$@

if [ ! -d "$src/" ]; then
	echo "root path ($src/) not exists"
	exit 1;
fi

# by default we don't use --checksum
rsync -av --delete --include="/data/***" --include="/cache/***" --include="/pushub/***" --exclude="*" $rsync_args "$src/" "$dest"
