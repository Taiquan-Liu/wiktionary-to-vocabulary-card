AUTOFLAKE_CMD = autoflake . \
	  --recursive \
	  --in-place \
	  --remove-all-unused-imports \
	  --ignore-init-module-imports \
	  --remove-unused-variables

lint:
	python setup_utils.py --lint
	$(AUTOFLAKE_CMD) --check
	black . --check --diff
	isort . --check --diff

fix-formatting:
	$(AUTOFLAKE_CMD)
	black .
	isort .
