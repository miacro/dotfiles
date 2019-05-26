if not functions -q fisher
    set -q XDG_CONFIG_HOME; or set XDG_CONFIG_HOME ~/.config
    curl https://git.io/fisher --create-dirs -sLo $XDG_CONFIG_HOME/fish/functions/fisher.fish
    fish -c fisher
end

# export OMF_HOME={$HOME}/.config/fish/omf
# echo $OMF_HOME
# curl https://get.oh-my.fish --create-dirs -fsLo {$OMF_HOME}/install
## sh -c "{$OMF_HOME}/install --path={$OMF_HOME}/oh-my-fish --config={$OMF_HOME}/config"
