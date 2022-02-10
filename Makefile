define run_migrations ## run migrations
	@- mkdir instance
	@ venv/bin/yoyo-migrate apply --all --batch
endef

define test_libgit ## Test libgit library
	echo "[*] testing libgit"
	cd libgit && cargo test --all --all-features --no-fail-fast
endef

define test_api_spec ## Test openapi specsheet
	@cd ./docs/openapi/  && yarn install 
	@cd ./docs/openapi/  && yarn test 
endef

define test_interface ## Run interface tests
	$(call run_migrations)
	@ . ./venv/bin/activate && pip install -e .
	@ . ./venv/bin/activate && pip install '.[test]'
	@ . ./venv/bin/activate && \
		DYNACONF_SERVER__DOMAIN="http://interface.example.com" \
		ENV_FOR_DYNACONF=testing \
		coverage run -m pytest && coverage html
	@ . ./venv/bin/activate && pip uninstall -y interface > /dev/null
endef

default: ## Run app
	. ./venv/bin/activate && cd libgit && maturin build
	. ./venv/bin/activate && python -m interface

coverage:
	# rustup component add llvm-tools-preview is required
	$(call test_interface)
	@. ./venv/bin/activate && ./scripts/coverage.sh --coverage
	@. ./venv/bin/activate && coverage xml && coverage html
	@. ./venv/bin/activate && ./scripts/coverage.sh --coverage

doc: ## Generates documentation
	@-rm -rf dist
	@-mkdir -p dist/openapi/
	@cd ./docs/openapi/ && yarn install && yarn html
	@cp -r ./docs/openapi/dist/* dist/openapi/

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
	@./venv/bin/black ./migrations/*
	@./venv/bin/black setup.py
	. ./venv/bin/activate && ./scripts/spellcheck.sh --check #--write

migrate: ## Run migrations
	$(call run_migrations)

test: ## Run tests
	@. ./venv/bin/activate && ./scripts/spellcheck.sh --check
	$(call	test_api_spec)
	$(call	test_libgit)
	$(call	test_interface)

test-interface: ## Run interface tests
	$(call	test_interface)
