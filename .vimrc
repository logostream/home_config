" Begin .vimrc
call pathogen#infect()
set hlsearch
filetype on
syntax on
set mouse=a
"set backspace=2 " make backspace work like most other apps
"set ttymouse=xterm2
" Color Schemes
if $TERM == 'linux'
    " Virtual Console
    colorscheme delek
else
    " Color terminal
    set t_Co=256
    colorscheme customleo
endif
hi Search guifg=white guibg=#4e9a06
hi Pmenu guibg=DarkMagenta
"set list listchars=tab:│\ ,trail:·,extends:>,eol:¶
set list listchars=tab:│\ ,trail:·,extends:>,eol:¬
set tabstop=4
set shiftwidth=4 " for cindent
"set expandtab
set autoindent
set cindent
set number
set guifont=monofur\ 13
set ignorecase
set smartcase
set virtualedit=onemore
" Always display statusline
set laststatus=2
" Highlight current line
set cursorline
"set cursorcolumn
"let g:Powerline_symbols = 'fancy'
"let g:Powerline_theme = 'solarized256'
let g:NERDTreeHijackNetrw = 0
au BufNewFile,BufRead *.nse set filetype=lua
" <F8> -- toggle taglist *taglist.txt*
nnoremap <silent> <F7> :NERDTreeToggle<CR>
nnoremap <silent> <F8> :TlistToggle<CR>
nnoremap <silent> <F9> :GundoToggle<CR><CR>:GundoFocus<CR>
nnoremap <Leader>av ggVG
nnoremap <Leader>ay gg"+yG
nnoremap <Leader>e :tabe %\| set foldcolumn=2<CR>
nnoremap <Leader>c :tabc<CR>
"nnoremap <Leader>p :tabp<CR>
"nnoremap <Leader>n :tabn<CR>
nnoremap <M-Down> :tabe %\| set foldcolumn=2<CR>
nnoremap <M-Up> :tabc<CR>
nnoremap <M-Left> :tabp<CR>
nnoremap <M-Right> :tabn<CR>
inoremap <M-Left> <Esc>:tabp<CR>
inoremap <M-Right> <Esc>:tabn<CR>
nnoremap <Leader><Down> :tabe %\| set foldcolumn=2<CR>
nnoremap <Leader><Up> :tabc<CR>
nnoremap <Leader><Left> :tabp<CR>
nnoremap <Leader><Right> :tabn<CR>
inoremap <Leader><Left> <Esc>:tabp<CR>
inoremap <Leader><Right> <Esc>:tabn<CR>
"nnoremap <Leader>s :w<CR>
"nnoremap <Leader>t :tabn
nnoremap <Leader>t1 :tabn1<CR>
nnoremap <Leader>t2 :tabn2<CR>
nnoremap <Leader>t3 :tabn3<CR>
nnoremap <Leader>t4 :tabn4<CR>
nnoremap <Leader>t5 :tabn5<CR>
nnoremap <Leader>t6 :tabn6<CR>
nnoremap <Leader>t7 :tabn7<CR>
nnoremap <Leader>t8 :tabn8<CR>
nnoremap <Leader>t9 :tabn9<CR>
nnoremap <Leader>y "+y
vnoremap <Leader>y "+y
nnoremap <Leader>p "+p
vnoremap <Leader>p "+p
nnoremap <Leader>fi :set foldmethod=indent<CR>
nnoremap <Leader>b :!echo 'backup as %~'; cp '%' '%~'; ls -l '%'*<CR>
nnoremap <Leader>h <C-W>h
nnoremap <Leader>j <C-W>j
nnoremap <Leader>k <C-W>k
nnoremap <Leader>l <C-W>l
" use <Tab> as <Esc> short cut
nnoremap <Tab> :
" <Tab>/<C-I> in default mode are used to forward jumplist, now we use <C-N> instead
nnoremap <C-N> <Tab>
vnoremap <Tab> <Esc>gV
onoremap <Tab> <Esc>
inoremap <Tab> <Esc>`^
" in urxvt may use <M-Tab> in insert mode instead
inoremap <Leader><Tab> <Tab>
cnoremap <S-Tab> <C-C>
" <C-B> in command is not very useful
cnoremap <C-B> <S-Tab>
" restore indent before hash
inoremap # <Tab><BS>#
" motion in command mode
cnoremap <Esc>b <S-Left>
cnoremap <Esc>f <S-Right>
cnoremap <M-B> <S-Left>
cnoremap <M-F> <S-Right>

set cinkeys-=0#
set indentkeys=-0#

" configures for plugins
"source $HOME/.vim/configs/neocomplcache.vim
source $HOME/.vim/configs/clang_complete.vim
" for plugin powerline
"set rtp+=~/.vim/bundle/powerline/powerline/bindings/vim

" python vim start from here
python << endpython
import vim;
import decimal;
endpython

" open uri under cursor
function! s:catch_uri()
	let uri = matchstr(expand("<cWORD>"), '[a-z]*:\/\/[^>\)]*') " for cWORD, see :help WORD
	echo uri
	return uri
endfunction

function! OpenUri(cmd)
	let uri = s:catch_uri()
	if a:cmd == 'new-xwin'
		execute "silent !topen --level=xwin " . uri . " 2>&1 > /dev/null"
		redraw!
	elseif a:cmd == 'new-term'
		execute "silent !topen --level=term " . uri
	elseif a:cmd == 'new-text'
		execute "silent !topen --level=text " . uri
	elseif a:cmd == 'new-tab'
		let path = system("topen --level=redir " . uri)
		execute "tabe " . path
	endif
endfunction
map <Leader>x :call OpenUri('new-xwin')<cr>
map <Leader>n :call OpenUri('new-term')<cr>
map <Leader>N :call OpenUri('new-text')<cr>
map <Leader>t :call OpenUri('new-tab')<cr>

function! s:python_substitute(cmd)
	" yank current visual selection to reg x
	normal gn
	redraw
	normal "xy
	let l:opt = ''
	while 1
		let l:opt = input('Replace? [Y]es [n]o: ')
		if l:opt == 'y' || l:opt == 'Y' || l:opt == ''
			break
		elseif l:opt == 'n'
			normal n
			return 1
		endif
	endwhile
	" prepare search pattern
	let l:pat = @/
	let l:head = matchstr(l:pat, '^^')
	let l:tail = matchstr(l:pat, '[\]\*$$')
	if !strlen(l:head)
		let l:pat = '^' . l:pat
	endif
	if strlen(l:tail) % 2
		let l:pat = l:pat . '$'
	endif
	" put new string value in reg x
	let g:pys_buf = @x
	let g:pys_groups = matchlist(g:pys_buf, l:pat)
	if len(g:pys_groups) == 0
		echoerr "Assert error in get g:pys_groups"
		return 0
	endif
python << endpython
def _python_local():
	cmd = vim.eval('a:cmd');
	buf = vim.vars['pys_buf'];
	s = vim.vars['pys_groups'];
	exec cmd;
	vim.vars['pys_buf'] = buf;
	return;
_python_local();
endpython
	" use global variable to avoid escap issue between vim and python
	let @x = g:pys_buf
	"re-select area and delete
	normal gnd
	"paste new string value back in
	normal "xP
	return 1
endfunction

function! s:python_substitute_global(cmd) range
	if strlen(@/) == 0
		return
	endif
	call cursor(a:firstline, 0)
	normal gnv
	let l:i = a:firstline
	while l:i <= a:lastline
		let l:j = line('.')
		"echo 'i, j: ' . l:i . ', ' . l:j
		if l:i == l:j
			if !s:python_substitute(a:cmd)
				break
			"else
			"	normal n
			endif
		else
			let l:i += 1
			"echo 'i: ' . l:i
		endif
	endwhile
	call cursor(a:firstline, 0)
endfunction

" all unmatched result will be folded out
com! -nargs=0 FoldFilter :set foldmethod=expr|set foldexpr=join(getline(max([0,v:lnum-5]),v:lnum+5))!~@/|normal zm
cnoreabbrev ff FoldFilter
nnoremap <Leader>ff :FoldFilter<CR>
com! -range=% -nargs=1 PySubs <line1>,<line2>call s:python_substitute_global("<args>")
cnoreabbrev pys PySubs
