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

add-word:
	@if [ -z "$(URL)" ]; then echo "Error: URL parameter required. Usage: make add-word URL=https://en.wiktionary.org/wiki/example"; exit 1; fi
	@echo "Processing $(URL)..."

	@# Extract word from URL
	$(eval WORD := $(shell echo "$(URL)" | sed -E 's|.*/wiki/([^/]+)|\1|' | sed 's/%C3%A4/ä/g' | sed 's/%C3%B6/ö/g' | sed 's/%C3%A5/å/g'))
	@echo "Word: $(WORD)"

	@# Download HTML
	@mkdir -p examples
	@wget -q "$(URL)" -O "examples/$(WORD).html"
	@echo "HTML saved to examples/$(WORD).html"

	@# Update examples.json
	@python -c "from wiktionary_vocab_card.utils import add_word; \
		add_word('$(WORD)', '$(URL)')"

	@# Generate vocabulary card
	@wikt-vocab generate "$(URL)" -o "examples/$(WORD).md"
	@echo "Generated examples/$(WORD).md"

regenerate-examples:
	@echo "Regenerating all example vocabulary cards..."
	@python -c "from wiktionary_vocab_card.utils import generate_all_examples; \
		generate_all_examples()"
	@echo "All examples regenerated successfully!"
