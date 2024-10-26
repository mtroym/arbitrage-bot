.PHONY: all install create_venv install_requirements format

# colored -----
YELLOW=\033[0;33m
GREEN=\033[0;32m
RESET=\033[0m

# --------------------
all: install

install: create_venv install_requirements

create_venv:
	@echo "Init virtual env..."
	@echo "Upgrading pip version..."
	@python3 -m pip install -U pip -q
	@python3 -m pip install virtualenv -q
	@if [ ! -d .venv ]; then \
		python3 -m virtualenv -q -p python3 ./.venv; \
		echo "Initialized ./.venv dir with system python3"; \
	else \
		echo "$(GREEN)Already created /.venv dir$(RESET)"; \
	fi
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(YELLOW)Please modify .env file to make it works.$(RESET)"; \
	else \
		echo "$(GREEN)Already created .env file$(RESET)"; \
		echo "Please compare it with $(GREEN).env.example$(RESET) to check if any envVars missing."; \
	fi
	

install_requirements:
	@echo "Using python bin from: $$(which python3)"
	@.venv/bin/python3 -m pip install -r requirements.txt -q
	@echo "Init env done."
	@echo "To activate the virtual environment, run:"
	@echo "$(YELLOW)source .venv/bin/activate$(RESET)"

format:
	@echo "Formatting Python code with pep8..."
	@python3 -m autopep8 ./ -r --in-place
	@echo "$(GREEN)Done!$(RESET)"

CHAIN_OPTION ?= base_mainnet

run:
	@echo "running monitor with $(CHAIN_OPTION)"
	@PYTHONPATH=$(PYTHONPATH):core python3 main.py --chain ${CHAIN_OPTION}

network:
	@python3 core/resource/providers.py