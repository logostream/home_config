#!/bin/sh

xrdb -merge ~/.Xresources          # update x resources db

#xscreensaver -no-splash &         # starts screensaver daemon 
xsetroot -cursor_name left_ptr &   # sets the cursor icon
xmodmap ~/.Xmodmap
#sh ~/.fehbg &                     # sets the background image
xset b off                         # disable the hardware beep

export XMODIFIERS="@im=ibus"
export GTK_IM_MODULE="ibus"
export QT_IM_MODULE="ibus"

exec /usr/bin/awesome
