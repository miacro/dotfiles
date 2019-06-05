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
function __my_setup_conda() {
  prefix=$(realpath $1)
  environment=$2
  if [ -f ${prefix}/etc/profile.d/conda.sh ]; then
    . ${prefix}/etc/profile.d/conda.sh
  fi

  if [[ -n ${environment} ]]; then
    pythondir=${prefix}/envs/${environment}/bin
  else
    pythondir=${prefix}/bin
  fi

  pythonprefix=$(dirname ${prefix})/anaconda-python
  pythoncommands=(python pip pydoc pytest pyvenv black blackd)
  mkdir -p ${pythonprefix}
  for item in ${pythoncommands}; do
    if [[ -x ${pythondir}/${item} ]]; then
      ln -sfn ${pythondir}/${item} ${pythonprefix}/${item}
    fi
  done
  export PATH=${pythonprefix}:${PATH}
}

__my_update_environments /usr/local
__my_update_environments ~/.local
__my_update_environments ~/.local/texlive/2018/bin/x86_64-linux
export PATH=${PATH}:/sbin:/usr/sbin:/usr/local/sbin
export PATH=~/node_modules/.bin:${PATH}
export PATH=~/bin:~/bin/private:~/bin/utils:${PATH}

__my_setup_conda ~/.local/anaconda3 ""

unset -f __my_update_environments
unset -f __my_find_bindirs
unset -f __my_setup_conda

export EDITOR="vim"
alias grep='grep --color=auto --exclude-dir=node_modules --exclude-dir=.cvs --exclude-dir=.git --exclude-dir=.hg --exclude-dir=.svn'
