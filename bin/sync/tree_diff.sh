#!/bin/bash
dir1=$1
shift
dir2=$1
shift
treeargs=$@
vimdiff <(cd "$dir1"; pwd; tree . $treeargs) <(cd "$dir2"; pwd; tree . $treeargs)
