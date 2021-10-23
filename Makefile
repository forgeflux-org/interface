default: ## Run app
	@. ./venv/bin/activate && FLASK_APP=interface/__init__.py FLASK_ENV=development flask run

env: ## Install all dependencies
	@-virtualenv venv
	. ./venv/bin/activate && pip install -r requirements.txt
	. ./venv/bin/activate && pip install -e .
	. ./venv/bin/activate && pip install '.[test]'

freeze: ## Freeze python dependencies
	@. ./venv/bin/activate && pip freeze > requirements.txt
	@-sed -i 's/interface.*/.\//' requirements.txt

help: ## Prints help for targets with comments
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

i: ## Launch app.py in an interactive python shell
	python -i ./interface/__init__.py

lint: ## Run linter
	@./venv/bin/black ./interface/*
	@./venv/bin/black ./tests/*

migrate: ## Run migrations
	@. ./venv/bin/activate && FLASK_APP=interface/__init__.py FLASK_ENV=development flask migrate

test: ## Run tests
	@pip install -e .
	@pip install '.[test]'
	@./venv/bin/pytest
