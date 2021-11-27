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
	codespell $FLAGS $PROJECT_ROOT/interface
	codespell $FLAGS $PROJECT_ROOT/tests
	codespell $FLAGS $PROJECT_ROOT/docs/openapi/api/
	codespell $FLAGS $PROJECT_ROOT/docs/openapi/openapi.yaml
	codespell $FLAGS $PROJECT_ROOT/README.md
	codespell $FLAGS --ignore-words-list crate .$PROJECT_ROOT/libgit/src
}

spell_check_misspell() {
	mkdir $TMP_DIR || true
	download
	$MISSPELL $FLAGS $PROJECT_ROOT/interface
	$MISSPELL $FLAGS $PROJECT_ROOT/tests
	$MISSPELL $FLAGS $PROJECT_ROOT/docs/openapi/api/
	$MISSPELL $FLAGS $PROJECT_ROOT/docs/openapi/openapi.yaml
	$MISSPELL $FLAGS $PROJECT_ROOT/README.md
	$MISSPELL $FLAGS -i crate .$PROJECT_ROOT/libgit/src
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
