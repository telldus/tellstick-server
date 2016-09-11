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
	sphinx-build -b html -d build/doctrees   docs build/html
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
	OUT=`python setup.py develop`
	local EXIT_CODE=$?
	if [ $EXIT_CODE -ne 0 ]; then
		echo $OUT
		echo "Could not install plugin"
		exit
	fi
	if [ -f $1/requirements.txt ]; then
		echo "Install requirements"
		pip install -U -r $1/requirements.txt
	fi
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
	PLUGINS="api base board developer live log telldus web"
	for plugin in $PLUGINS; do
		PLUGINPATH="$BASEDIR/$plugin"
		installPlugin $PLUGINPATH
	done
}

setupVirtualEnv() {
	if [ -d $BASEDIR/build/env ]; then
		source $BASEDIR/build/env/bin/activate
		return
	fi
	echo "Create virtualenv"
	virtualenv build/env
	source $BASEDIR/build/env/bin/activate
	pip install -U pip
}

checkPrerequisites
setupVirtualEnv

case $1 in
	build-docs)
		echo "Building docs"
		buildDocs
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
	*)
		echo "Unknown command $1"
esac
