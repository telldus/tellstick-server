#!/bin/bash

getAbsolutePath() {
	# $1 : relative filename
	if [ -d "$(dirname "$1")" ]; then
		echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
	fi
}

BASEDIR=$(dirname $(getAbsolutePath "$0"))
export HWBOARD=desktop

buildDocs() {
	SPHINX=`which sphinx-build`
	if [ "$SPHINX" == "" ]; then
		echo "Install Sphinx"
		pip install -U -r docs/requirements.txt
	fi
	COMMAND=sphinx-build
	while [[ $# -gt 0 ]]; do
		case $1 in
			-w|--watch)
			AUTOBUILD=`which sphinx-autobuild`
			if [ "$AUTOBUILD" == "" ]; then
				pip install sphinx-autobuild
			fi
			COMMAND="sphinx-autobuild -B -z api -z base -z board -z developer -z live -z log -z sdk -z telldus -z web"
			shift
			;;
			*)
			shift
			;;
		esac
	done
	$COMMAND -E -b html -d build/doctrees  docs build/html
}

buildPlugin() {
	PLUGINPATH=$(getAbsolutePath "$1")
	shift
	echo "Building plugin $PLUGINPATH"
	cd $PLUGINPATH
	OUT=`python setup.py telldus_plugin "$@"`
	local EXIT_CODE=$?
	if [ $EXIT_CODE -ne 0 ]; then
		echo $OUT
		echo "Could not build plugin"
		exit
	fi
}

checkPrerequisites() {
	VIRTUALENV=`which virtualenv`
	if [ "$VIRTUALENV" == "" ]; then
		echo "virtualenv could not be found in the system."
		echo "Please install it with:"
		echo
		echo "sudo easy_install virtualenv"
		exit 1
	fi
}

installPlugin() {
	echo "Installing plugin $1"
	cd $1
	if [ -f $1/requirements.txt ]; then
		echo "Install requirements"
		pip install -U -r $1/requirements.txt
	fi
	OUT=`python setup.py develop`
	local EXIT_CODE=$?
	if [ $EXIT_CODE -ne 0 ]; then
		echo $OUT
		echo "Could not install plugin"
		exit
	fi
	if [ -f $1/package.json ]; then
		echo "Install npm packages"
		npm install
		npm run build
	fi
}

printHelp() {
	echo -e "Usage: $0 command [arguments]"
	echo
	echo -e "Command chould be one of:"
	echo -e "  build-docs:\tBuilds the documentation to build/html. Usage:"
	echo -e "  \t\t  $0 build-docs [--watch]"
	echo -e "  \t\t  If --watch is supplied the files will be monitored and rebuilt when changed."
	echo -e "  build-plugin:\tBuild a distributable plugin from a plugin dir. Usage:"
	echo -e "  \t\t  $0 build-plugin [path-to-plugin]"
	echo -e "  \t\t  where [path-to-plugin] should be the path to the plungins root folder"
	echo -e "  help:\t\tShows this help"
	echo -e "  install:\tInstall a plugin. Usage:"
	echo -e "  \t\t  $0 install [path-to-plugin]"
	echo -e "  \t\t  where [path-to-plugin] should be the path to the plungins root folder"
	echo -e "  run:\t\tStarts the server"
	echo -e "  \t\t  The server will be restarted automatically when a file changes"
	echo -e "  setup:\tSets up the virtualenv and installs a minium set of required plugins"
	echo -e "  shell:\tStarts a new shell with the virtualenv activated"
	echo -e "  test:\tRun unit testing"
	echo -e "  uninstall:\tUninstall a plugin. Usage:"
	echo -e "  \t\t  $0 uninstall [plugin-name]"
	echo -e "  \t\t  where [plugin-name] is the name of the plugin."
}

run() {
	local EXIT_CODE=0
	while [ $EXIT_CODE -eq 0 ]; do
		python run.py
		EXIT_CODE=$?
		sleep 2
	done
}

setup() {
	PLUGINS="api base board developer live log sdk telldus web"
	pip install -U -r requirements.txt

	for plugin in $PLUGINS; do
		PLUGINPATH="$BASEDIR/$plugin"
		installPlugin $PLUGINPATH
	done
	# Setup git commit hooks
	captainhook install --use-virtualenv-python
}

setupVirtualEnv() {
	if [ -d $BASEDIR/build/env ]; then
		source $BASEDIR/build/env/bin/activate
		return
	fi
	echo "Create virtualenv"
	virtualenv --python=python2.7 build/env
	source $BASEDIR/build/env/bin/activate
	pip install -U pip
}

checkPrerequisites
setupVirtualEnv

case $1 in
	build-docs)
		shift
		echo "Building docs"
		buildDocs "$@"
	;;
	build-plugin)
		shift
		buildPlugin "$@"
	;;
	help)
		printHelp
	;;
	install)
		echo "Installing plugin from $2"
		PLUGINPATH=$(getAbsolutePath "$2")
		installPlugin $PLUGINPATH
	;;
	run)
		echo "Starting server"
		run
	;;
	setup)
		echo "Setting up environment"
		setup
	;;
	shell)
		echo "Starting sandboxed shell"
		PS1='(TellStick) \[\033[01;32m\]\u@\h\[\033[01;34m\] \$\[\033[00m\] '
		sh
	;;
	test)
		python -m unittest tests
	;;
	uninstall)
		pip uninstall $2
	;;
	*)
		echo "Unknown command $1"
		printHelp
esac
