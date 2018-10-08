#!/bin/sh
if [ -d /etc/X11/xinit/xinitrc.d ]; then
  for f in /etc/X11/xinit/xinitrc.d/*; do
    [ -x "$f" ] && . "$f"
  done
  unset f
fi

[[ -f ~/.Xresources ]] && xrdb -merge ~/.Xresources 
eval "$(dbus-launch --sh-syntax --exit-with-session)"
[[ -f ~/.xcommonrc ]] && source ~/.xcommonrc

# exec ck-launch-session dbus-launch --sh-syntax --exit-with-session awesome
# export KDEWM=awesome
exec ~/.stumpwm.d/bin/stumpwm
exec awesome
# exec enlightenment_start
# exec gnome-session
# exec startkde 
# exec startxfce4
# exec startlxde
# exec startfluxbox 
# exec ck-launch-session dbus-launch --sh-syntax --exit-with-session fvwm
