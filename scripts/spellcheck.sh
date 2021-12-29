#!/bin/bash
readonly MISSPELL_DOWNLOAD="https://github.com/client9/misspell/releases/download/v0.3.4/misspell_0.3.4_linux_64bit.tar.gz"
readonly TMP_DIR=$(pwd)/tmp
readonly PROJECT_ROOT=$(pwd)
readonly MISSPELL_TARBALL="$TMP_DIR/misspell.tar.bz2"
readonly MISSPELL="$TMP_DIR/misspell"

set -Eeuo pipefail

source $(pwd)/scripts/lib.sh

FLAGS=""

download() {
	if [ ! -e $MISSPELL ]; 
	then 
		echo "[*] Downloading misspell"
		wget --quiet  --output-doc=$MISSPELL_TARBALL $MISSPELL_DOWNLOAD;
		cd $TMP_DIR
		tar -xf $MISSPELL_TARBALL;
		cd $PROJECT_ROOT
	fi
}

spell_check_codespell() {
	_check(){
		codespell $FLAGS --ignore-words-list=$1 $PROJECT_ROOT/$2 || true
	}
	_check KeyPair interface
	_check KeyPair tests
	_check KeyPair docs/openapi/api/
	_check KeyPair docs/openapi/openapi.yaml
	_check KeyPair README.md
	_check crate   libgit/src
}

spell_check_misspell() {
	mkdir $TMP_DIR || true
	download

	_check(){
		$MISSPELL $FLAGS -i $1 $PROJECT_ROOT/$2 || true
	}

	_check KeyPair interface
	_check KeyPair tests
	_check KeyPair docs/openapi/api/
	_check KeyPair docs/openapi/openapi.yaml
	_check KeyPair README.md
	_check crate libgit/src
}

check_arg $1

if match_arg $1 'w' '--write'
then
	echo "[*] checking and correcting spellings"
	FLAGS="-w"
	spell_check_misspell
	spell_check_codespell
elif match_arg $1 'c' '--check'
then
	echo "[*] checking spellings"
	spell_check_misspell
	spell_check_codespell
else
	echo "undefined option"
	exit 1
fi
