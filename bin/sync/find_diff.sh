#!/bin/bash
dir1=$1
shift
dir2=$1
shift
findargs=$@
vimdiff <(cd "$dir1"; pwd; find . $findargs | sort) <(cd "$dir2"; pwd; find . $findargs | sort)
