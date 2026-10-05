run:
	uv run 42-rag-against-the-machine $(ARGS)

index:
	uv run 42-rag-against-the-machine index

search:
	uv run 42-rag-against-the-machine search "where will i be able to see the benchmark results" --k 10

search_dataset:
	uv run 42-rag-against-the-machine search_dataset --dataset_path ./downloads/datasets_public/UnansweredQuestions/dataset_docs_public.json --save_directory data/answer --k 5


install:
	uv sync

debug:
	uv run $(py) -m pdb src

lint: 
	uv run flake8 . && mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs