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
nnoremap <Leader>t :tabn
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
" <Leader>fx -- all unmatched result will be folded out
" nnoremap <Leader>fx :set foldmethod=expr\| set foldexpr=join(getline(max([0,v:lnum-5]),v:lnum))!~@/<CR>
com -nargs=1 FoldFilter :/<args>/|set foldmethod=expr|set foldexpr=join(getline(max([0,v:lnum-5]),v:lnum+5))!~'<args>'
nnoremap <Leader>fi :set foldmethod=indent<CR>
nnoremap <Leader>b :!echo 'backup as %~'; cp '%' '%~'; ls -l '%'*<CR>
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
set cinkeys-=0#
set indentkeys=-0#

" configures for plugins
"source $HOME/.vim/configs/neocomplcache.vim
source $HOME/.vim/configs/clang_complete.vim
