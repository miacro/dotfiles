#!/bin/sh
function __my_update_environments() {
  prefix=$1
  export LIBRARY_PATH=${prefix}/lib:${prefix}/lib64:${LIBRARY_PATH}
  export LD_LIBRARY_PATH=${prefix}/lib:${prefix}/lib64:${LD_LIBRARY_PATH}
  export C_INCLUDE_PATH=${prefix}/include:${C_INCLUDE_PATH}
  export CPLUS_INCLUDE_PATH=${prefix}/include:${C_INCLUDE_PATH}
  export PATH=${prefix}/bin:${PATH}
  export MANPATH=${prefix}/share/man:${MANPATH}
  export INFOPATH=${prefix}/share/info:${INFOPATH}
}

function __my_find_bindirs() {
  prefix=$1
  echo $(find -L ${prefix} \
              -regex "$(realpath ${prefix}).*/bin" \
              -type d \
              -printf %p:)
}

__my_update_environments /usr/local
__my_update_environments ~/.local
[[ -f ~/.profile.d/texlive ]] && source ~/.profile.d/texlive
export PATH=${PATH}:/sbin:/usr/sbin:/usr/local/sbin
export PATH=~/node_modules/.bin:${PATH}
export PATH=~/bin:~/bin/private:~/bin/utils:${PATH}

unset -f __my_update_environments
unset -f __my_find_bindirs

export EDITOR="vim"
alias grep='grep --color=auto --exclude-dir=node_modules --exclude-dir=.cvs --exclude-dir=.git --exclude-dir=.hg --exclude-dir=.svn'
