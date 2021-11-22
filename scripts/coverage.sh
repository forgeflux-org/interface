#!/bin/bash
readonly GRCOV_DOWNLOAD="https://github.com/mozilla/grcov/releases/download/v0.8.2/grcov-linux-x86_64.tar.bz2"
readonly TMP_DIR=$(pwd)/tmp
readonly PROJECT_ROOT=$(pwd)/libgit
readonly GRCOV_TARBAL="$TMP_DIR/grcov.tar.bz2"
readonly GRCOV="$TMP_DIR/grcov"

export DYNACONF_SYSTEM__NORTHSTAR="http://$(hostname):3000"
export DYNACONF_SERVER__DOMAIN="http://$(hostname):7000"

clean_up() {
	cd $PROJECT_ROOT
	/bin/rm default.profraw  lcov.info *.profraw || true
	cd target
	/bin/rm default.profraw  lcov.info *.profraw || true
	cargo clean
}

download() {
	if [ ! -e $GRCOV ]; 
	then 
		echo "[*] Downloading grcov"
		wget --quiet  --output-doc=$GRCOV_TARBAL $GRCOV_DOWNLOAD;
		cd $TMP_DIR
		tar -xf $GRCOV_TARBAL;
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
		--ignore "../*" -o target/lcov.info
}

coverage() {
	cd $PROJECT_ROOT
	mkdir $TMP_DIR || true
	clean_up
	download
	build_and_test
	source ./venv/bin/activate  && coverage html
	source ./venv/bin/activate  && coverage xml
}

run_tests() {
	docker-compose up -d
	cd libgit && cargo test --all --all-features --no-fail-fast > /dev/null
	source ./venv/bin/activate && pip install -e . > /dev/null
	source ./venv/bin/activate && pip install '.[test]' > /dev/null
	python -m interface& > /dev/null
	coverage run -m pytest
	kill $(pgrep -a -f "python -m interface") || true
	pip uninstall -y interface > /dev/null
	docker-compose down
}

while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
    -c|--coverage)
	  echo "[*] Generating coverage report"
	  run_tests
	  coverage
	  break
      ;;
    -t|--test)
	  echo "[*] Running tests"
	  run_tests
	  break
      ;;
  esac
done
