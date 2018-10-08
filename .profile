export LIBRARY_PATH=~/.local/lib:~/.local/lib64:${LIBRARY_PATH}
export LD_LIBRARY_PATH=~/.local/lib:~/.local/lib64:${LD_LIBRARY_PATH}
export C_INCLUDE_PATH=~/.local/include:${C_INCLUDE_PATH}
export CPLUS_INCLUDE_PATH=~/.local/include:${C_INCLUDE_PATH}

# FINDDIR=~/.local
# echo $(find -L ${FINDDIR} \
#             -regex "$(realpath ${FINDDIR})/.*/bin" \
#             -type d \
#             -printf %p:)
export PATH=${PATH}:/sbin:/usr/sbin:/usr/local/sbin
export PATH=~/node_modules/.bin:${PATH}
export PATH=~/.local/bin:${PATH}
export PATH=~/.local/texlive/2018/bin/x86_64-linux:${PATH}
export PATH=~/bin:~/bin/private:~/bin/utils:${PATH}

export MANPATH=${MANPATH}:~/.local/share/man
export MANPATH=${MANPATH}:~/.local/texlive/2018/texmf-dist/doc/man

export INFOPATH=${INFOPATH}:~/.local/share/info
export INFOPATH=${INFOPATH}:~/.local/texlive/2018/texmf-dist/doc/info

export EDITOR="vim" 
alias grep='grep --color=auto --exclude-dir=node_modules --exclude-dir=.cvs --exclude-dir=.git --exclude-dir=.hg --exclude-dir=.svn'
