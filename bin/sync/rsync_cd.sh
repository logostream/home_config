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

rsync -av --delete --include="/data/***" --include="/cache/***" --include="/tagged" --include="/Copy/***" --exclude="*" $rsync_args "$src/" "$dest"
