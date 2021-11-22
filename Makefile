default: ## Run app
	. ./venv/bin/activate && cd libgit && maturin build
	. ./venv/bin/activate && python -m interface

coverage: migrate
	# rustup component add llvm-tools-preview is required
	./scripts/coverage.sh --coverage

docker: ## Build Docker image from source
	docker build -t forgedfed/interface .

env: ## Install all dependencies
	@-virtualenv venv
	. ./venv/bin/activate && pip install maturin
	. ./venv/bin/activate && cd libgit && maturin develop
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
	@./venv/bin/black ./tests/*

migrate: ## Run migrations
	@- mkdir instance
	@ venv/bin/yoyo-migrate apply --all --batch

test: migrate ## Run tests
	@./scripts/coverage.sh -t
