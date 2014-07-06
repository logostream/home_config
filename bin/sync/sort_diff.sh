#!/bin/bash
f1=$1
shift
f2=$1
shift
diffargs=$@
diff <(sort $f1) <(sort $f2) $diffargs
if [ "$?" -gt 1 ]
then
	exit 1;
else
	exit 0;
fi
