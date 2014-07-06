#!/bin/bash
logpath=$1
tail -f $logpath | grep '\<step\>\|^err\>\|^warn\>'
