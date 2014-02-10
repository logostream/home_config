@echo off
set /p line=
echo %line% | C:\cygwin\bin\sed -e "s_^\([a-z]\):_/cygdrive/\L\1_gI" -e "s_\\\\_/_g"