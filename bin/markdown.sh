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
markdown_py -x extra `# include def_list, tables, attr_list` \
    -x mathjax -x topen -x preview -x tag -x anchor \
    -x 'poptoc(title=Table of Content (Beta),maxlevel=2)' \
    -x 'wikilinks(base_url=http://en.wikipedia.org/wiki/, end_url=)' \
    -x highlight -x githubcss $path > $htmlpath \
