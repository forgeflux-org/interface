default: ## Run app
	cd libgit && maturin build
	. ./venv/bin/activate && python -m interface

coverage: test
	# rustup component add llvm-tools-preview is required
	@./scripts/coverage.sh
	@ . ./venv/bin/activate  && coverage html
	@ . ./venv/bin/activate  && coverage xml

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
	@- mkdir instance
	@ venv/bin/yoyo-migrate apply --all --batch

test: migrate ## Run tests
	@docker-compose up -d
	@cd libgit && cargo test --all --all-features --no-fail-fast
	@. ./venv/bin/activate && pip install -e .
	@. ./venv/bin/activate && pip install '.[test]'
	@ ./interface/__main__.py &
	@pip install -e .
	@pip install '.[test]'
	@ . ./venv/bin/activate && coverage run -m pytest
	@- kill -9 $(pgrep  -f interface)
	@pip uninstall -y interface
	@docker-compose down
