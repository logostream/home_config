#!/bin/bash
f1=$1
echo "$f1" | md5sum | sed 's/^\([a-z0-9]*\).*/\1/' > $f1
