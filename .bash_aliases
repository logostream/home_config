#!/bin/bash
alias tmuxat='tmux attach-session -t'
alias tmuxld='~/.tmux/load'
alias tmuxs='tmux list-sessions'
alias pfgrep='ps -ef | grep'
alias hiblock="sudo hibernate --lock-console-as $USER"
alias ifconfig='/sbin/ifconfig'
alias man='TERM=xterm man' # fix highlight issue in tmux
# command for start agent of copy.com as deamon
alias copydemon='nohup ~/bin/copy/x86_64/CopyConsole -debug -daemon > ~/log/copy.log &'
alias unzip-gbk='unzip -O CP936'
