SHELL=/bin/bash
MAKE=make --no-print-directory

ACTION=reinstall
INSTALLER=stow

TARGET_DIR=${HOME}
PACKAGE=miacro
PACKAGE_DIR=home
STOW_OPTIONS=

install-dotfiles:
	@${MAKE} stow-${ACTION} \
	&& ${MAKE} install-powerline

ln-reinstall:
	@${MAKE} ln-uninstall \
	&& ${MAKE} ln-install

ln-install:
	@[[ ! -L ${TARGET_DIR}/${PACKAGE} ]] && [[ ! -f ${TARGET_DIR}/${PACKAGE} ]] \
	&& ln -s $(realpath ${PACKAGE_DIR}/${PACKAGE}) ${TARGET_DIR}/${PACKAGE}

ln-uninstall:
	@[[ -L ${TARGET_DIR}/${PACKAGE} ]] \
	&& rm -f ${TARGET_DIR}/${PACKAGE} \
	|| exit 0

stow-reinstall:
	@${MAKE} STOW_OPTIONS=-R stow

stow-install:
	@${MAKE} STOW_OPTIONS= stow

stow-uninstall:
	@${MAKE} STOW_OPTIONS=-D stow

stow:
	stow -d ${PACKAGE_DIR} -t ${TARGET_DIR} ${STOW_OPTIONS} ${PACKAGE}

install-powerline:
#	@pip install --upgrade --user git+git://github.com/powerline/powerline
	@pip install --upgrade --user powerline-status

.PHONY: install-dotfiles install-portage install-powerline
