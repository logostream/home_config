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
alias gds='go_dirs.py'
alias gcd='fun_go_cd'
alias gpushd='fun_go_pushd'

# sync tools
alias phub='~/bin/sync/pushub.sh'
alias lhub='~/bin/sync/linkhub.py'

# functions
fun_go_cd() {
	target=$(go_dirs.py $1)
	cd $target
}
fun_go_pushd() {
	target=$(go_dirs.py $1)
	pushd $target
}
