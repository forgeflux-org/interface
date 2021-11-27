#!/bin/bash

set -Eeuo pipefail

source $(pwd)/scripts/lib.sh

FLAGS=""

spell_check() {
	codespell $FLAGS ./interface
	codespell $FLAGS ./tests
	codespell $FLAGS ./docs/openapi/api/
	codespell $FLAGS ./docs/openapi/openapi.yaml
	codespell $FLAGS --ignore-words-list crate ./libgit/src
}

check_arg $1

if match_arg $1 'w' '--write'
then
	echo "[*] checking and correcting spellings"
	FLAGS="${FLAGS} --write-changes"
	echo $FLAGS
	spell_check
elif match_arg $1 'c' '--check'
then
	echo "[*] checking spellings"
	spell_check
else
	echo "undefined option"
	exit 1
fi
