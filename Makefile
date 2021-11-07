LLVM_PROFILE_FILE = libgit-%p-%m.profraw
COVERAGE_RUSTFLAGS = "-Zinstrument-coverage"
GRCOV_DOWNLOAD = "https://github.com/mozilla/grcov/releases/download/v0.8.2/grcov-linux-x86_64.tar.bz2"
GRCOV_TARBAL = "grcov.tar.bz2"
GRCOV = "grcov"

default: ## Run app
	cd libgit && maturin build
	. ./venv/bin/activate && python -m interface

coverage:
	# rustup component add llvm-tools-preview is required
	@- cd libgit && /bin/rm default.profraw  lcov.info
	@if [[ ! -e $(GRCOV) ]]; then \
		wget --quiet  --output-doc=$(GRCOV_TARBAL) $(GRCOV_DOWNLOAD); \
			tar -xf $(GRCOV_TARBAL); \
	fi
	RUSTFLAGES=$(COVERAGE_RUSTFLAGS) cd libgit && \
			   cargo build &&  \
			   cargo test --all --all-features --no-fail-fast
	LLVM_PROFILE_FILE=$(LLVM_PROFILE_FILE) \
	RUSTFLAGES=$(COVERAGE_RUSTFLAGS) \
	  cd libgit && \
	  ../grcov . --binary-path ./target/debug/ \
	  -s . -t lcov --branch --ignore-not-existing --ignore "/*" -o lcov.info

docker: ## Build Docker image from source
	docker build -t forgedfed/interface .

env: ## Install all dependencies
	@-virtualenv venv
	pip install maturin
	cd libgit && maturin develop
	. ./venv/bin/activate && pip install -r requirements.txt
#	. ./venv/bin/activate && pip install -e .
	#. ./venv/bin/activate && pip install '.[test]'

freeze: ## Freeze python dependencies
	@. ./venv/bin/activate && pip freeze > requirements.txt
	@-sed -i 's/.*fedv2\/interface.*/.\//' requirements.txt
	@-sed -i '/libgit.*/d' requirements.txt

help: ## Prints help for targets with comments
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

i: ## Launch app.py in an interactive python shell
	python -i ./interface/__init__.py

lint: ## Run linter
	@./venv/bin/black ./interface/*
	#@./venv/bin/black ./tests/*

migrate: ## Run migrations
	@. ./venv/bin/activate && FLASK_APP=interface/__init__.py FLASK_ENV=development flask migrate

#test: ## Run tests
#	@cd ./docs/openapi/  && yarn install 
#	@cd ./docs/openapi/  && yarn test 
#	@pip install -e .
#	@pip install '.[test]'
#	@./venv/bin/pytest
