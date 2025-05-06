#!/bin/sh
__my_update_environments() {
  prefix=$1
  export LIBRARY_PATH=${prefix}/lib:${prefix}/lib64:${LIBRARY_PATH}
  export LD_LIBRARY_PATH=${prefix}/lib:${prefix}/lib64:${LD_LIBRARY_PATH}
  export C_INCLUDE_PATH=${prefix}/include:${C_INCLUDE_PATH}
  export CPLUS_INCLUDE_PATH=${prefix}/include:${C_INCLUDE_PATH}
  export PATH=${prefix}/bin:${PATH}
  export MANPATH=${prefix}/share/man:${MANPATH}
  export INFOPATH=${prefix}/share/info:${INFOPATH}
}

__my_find_bindirs() {
  prefix=$1
  echo $(find -L ${prefix} \
              -regex "$(realpath ${prefix}).*/bin" \
              -type d \
              -printf %p:)
}

if [ ! -n "${__INITIALIZED_PROFILE__}" ]; then
  __my_update_environments /usr/local
  __my_update_environments ~/.local

  [ -f ~/.profile.d/all-init ] && . ~/.profile.d/all-init

  export PATH=${PATH}:/sbin:/usr/sbin:/usr/local/sbin
  export PATH=~/node_modules/.bin:${PATH}
  export PATH=~/bin:~/bin/private:~/bin/utils:${PATH}

  unset -f __my_update_environments
  unset -f __my_find_bindirs
  __INITIALIZED_PROFILE__=1
fi

export EDITOR="vim"
alias grep='grep --color=auto --exclude-dir=node_modules --exclude-dir=.cvs --exclude-dir=.git --exclude-dir=.hg --exclude-dir=.svn'
[ -f /etc/profile.d/autojump.sh ] && source /etc/profile.d/autojump.sh
