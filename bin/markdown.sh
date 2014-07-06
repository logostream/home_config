#!/bin/bash
path=$1
if [ ! -f "$path" ]; then
	echo "markdown path ($path) not exists"
	exit 1;
fi
filename=$(basename "$path")
dirname=$(dirname "$path")
htmlname="${filename%.*}"
htmlpath="$dirname/${htmlname}.html"
export PYTHONPATH="$HOME/bin/mdx"
markdown_py -x toc -x extra -x mathjax $path > $htmlpath
