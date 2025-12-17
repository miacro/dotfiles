fpath=(
  ~/.config/zsh/completions
  ~/.config/zsh/functions
  ~/.config/zsh/site-functions
  $fpath
)

for fp in \
  /usr/share/zsh/site-functions
do
  if [ -d "$fp" ]; then
    fpath=($fpath $fp)
  fi
done
unset fp
