readonly GRCOV_DOWNLOAD="https://github.com/mozilla/grcov/releases/download/v0.8.2/grcov-linux-x86_64.tar.bz2"
readonly GRCOV_TARBAL="grcov.tar.bz2"
readonly GRCOV="grcov"

readonly PROJECT_ROOT=$(pwd)/libgit

clean_up() {
	cd $PROJECT_ROOT
	/bin/rm default.profraw  lcov.info || true
	cd $cur_dir
}

download() {
	if [ ! -e $GRCOV ]; 
	then 
		echo "[*] Downloading grcov"
		wget --quiet  --output-doc=$GRCOV_TARBAL $GRCOV_DOWNLOAD;
		tar -xf $GRCOV_TARBAL;
	fi
}

build_and_test() {
	RUSTFLAGES="-Zinstrument-coverage"
	LLVM_PROFILE_FILE="libgit-%p-%m.profraw"

	cd $PROJECT_ROOT
	echo "[*] Building project"
	cargo build

	echo "[*] Running tests"
    cargo test --all --all-features --no-fail-fast

	echo "[*] Generating coverage"
	../$GRCOV . --binary-path  \
		./target/debug/ \
		-s . -t lcov --branch \
		--ignore-not-existing \
		--ignore "/*" -o lcov.info
}

clean_up
download
build_and_test
