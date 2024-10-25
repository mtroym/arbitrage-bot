.PHONY: all install create_venv install_requirements

all: install

install: create_venv install_requirements

create_venv:
	@echo "Installing requirements."
	@python3 -m pip install -U pip -q
	@python3 -m pip install virtualenv -q
	@if [ ! -d .venv ]; then \
		python3 -m virtualenv -q -p python3 .venv; \
		echo "Initialized /.venv dir with system python3"; \
	else \
		echo "Already created /.venv dir"; \
	fi

install_requirements:
	@echo "Using python bin from: $$(which python3)"
	@.venv/bin/python3 -m pip install -r requirements.txt -q
	@echo "Init env done. To activate the virtual environment, run:"
	@echo "$(GREEN)source .venv/bin/activate$(RESET)"

