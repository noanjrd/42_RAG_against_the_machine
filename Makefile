run:
	uv run 42-rag-against-the-machine $(ARGS)

index:
	uv run 42-rag-against-the-machine index

search:
	uv run 42-rag-against-the-machine search "what is x" --k 10

install:
	uv sync

debug:
	uv run $(py) -m pdb src

lint: 
	uv run flake8 . && mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs