.PHONY: install
install:
	uv sync --all-extras

.PHONY: lint
lint:
	uv run -- ruff check
	uv run -- ruff format --diff
	uv run -- ty check
	uv run -- pyright

.PHONY: serve-documentation
serve-documentation:
	uv run -- mkdocs serve --config-file docs/mkdocs.yml --strict --livereload