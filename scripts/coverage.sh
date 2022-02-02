#!/bin/bash
readonly GRCOV_DOWNLOAD="https://github.com/mozilla/grcov/releases/download/v0.8.6/grcov-v0.8.6-aarch64-unknown-linux-gnu.tar.gz"
readonly TMP_DIR=$(pwd)/tmp
readonly PROJECT_ROOT=$(pwd)/libgit
readonly GRCOV_TARBAL="$TMP_DIR/grcov.tar.gz"
readonly GRCOV="$TMP_DIR/grcov"

source $(pwd)/scripts/lib.sh

download() {
	if [ ! -e $GRCOV ]; 
	then 
		echo "[*] Downloading grcov"
		wget --quiet  --output-doc=$GRCOV_TARBAL $GRCOV_DOWNLOAD;
		cd $TMP_DIR
		tar -xvzf $GRCOV_TARBAL;
		cd $PROJECT_ROOT
	fi
}

build_and_test() {
	export RUSTFLAGS="-Zinstrument-coverage"
	cd $PROJECT_ROOT

	echo "[*] Building project"
	cargo build

	export LLVM_PROFILE_FILE="target/libgit-%p-%m.profraw"

	echo "[*] Running tests"
    cargo test

	echo "[*] Generating coverage"
	$GRCOV target/ --binary-path  \
		./target/debug/ \
		-s . -t lcov --branch \
		--ignore-not-existing \
        --ignore src/error.rs \
		--ignore "../*" -o target/lcov.info

	$GRCOV . -s . --binary-path \
		./target/debug/ \
		-t html --branch \
		--ignore-not-existing \
        --ignore src/error.rs \
		-o ./target/debug/coverage/ || true
}

run_coverage() {
	cd $PROJECT_ROOT
	mkdir $TMP_DIR || true
	clean_up
	download
	build_and_test
}

check_arg $1

if match_arg $1 'c' '--coverage'
then
	run_coverage
else
	echo "undefined option"
	exit 1
fi
