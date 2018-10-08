SOURCE_DIR=`pwd`
TARGET_DIR=${HOME}/.config/awesome
MAKE=make --no-print-directory
SHELL=/bin/bash

reinstall:
	@  ${MAKE} uninstall \
	&& ${MAKE} install

install:
	@  ${MAKE} MODULE=miacro  install_module \
	&& ${MAKE} MODULE=rc.lua install_module

uninstall:
	@  ${MAKE} MODULE=miacro uninstall_module \
	&& ${MAKE} MODULE=rc.lua uninstall_module

install_module: prepare_target
	@  [[ ! -L ${TARGET_DIR}/${MODULE} ]] && [[ ! -f ${TARGET_DIR}/${MODULE} ]] \
	&& ln -s ${SOURCE_DIR}/${MODULE} ${TARGET_DIR}/${MODULE} \
	||  exit 0

uninstall_module: prepare_target
	@  [[ -L ${TARGET_DIR}/${MODULE} ]] \
	&& rm ${TARGET_DIR}/${MODULE} \
	|| exit 0

prepare_target:
	@  [[ ! -d ${TARGET_DIR} ]] \
	&& mkdir -p ${TARGET_DIR} \
	|| exit 0

.PHONY: reinstall uninstall install install_module uninstall_module prepare_target
