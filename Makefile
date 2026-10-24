run:
	uv run 42-rag-against-the-machine $(ARGS)

index:
	uv run 42-rag-against-the-machine index

search:
	uv run 42-rag-against-the-machine search "where will i be able to see the benchmark results" --k 10

search_dataset_docs:
	HF_HUB_OFFLINE=1 uv run 42-rag-against-the-machine search_dataset --dataset_path ./downloads/datasets_public/UnansweredQuestions/dataset_docs_public.json --save_directory data/output/search_results/UnansweredQuestions --k 10

search_dataset_code:
	HF_HUB_OFFLINE=1 uv run 42-rag-against-the-machine search_dataset --dataset_path ./downloads/datasets_public/UnansweredQuestions/dataset_code_public.json --save_directory data/output/search_results/UnansweredQuestions --k 10

answer:
	HF_HUB_OFFLINE=1 uv run 42-rag-against-the-machine answer "what are the standards?" --k 5

answer_dataset_docs:
	uv run 42-rag-against-the-machine answer_dataset --student_search_results_path data/output/search_results/UnansweredQuestions/dataset_docs_public.json --save_directory data/output/search_results_and_answer/UnansweredQuestions

answer_dataset_code:
	uv run 42-rag-against-the-machine answer_dataset --student_search_results_path data/output/search_results/UnansweredQuestions/dataset_code_public.json --save_directory data/output/search_results_and_answer/UnansweredQuestions

evaluate_docs:
	uv run 42-rag-against-the-machine evaluate --student_search_results_path data/output/search_results/UnansweredQuestions/dataset_docs_public.json --dataset_path data/datasets/AnsweredQuestions/dataset_docs_public.json


install:
	uv sync

debug:
	uv run $(py) -m pdb src

lint: 
	uv run flake8 src && mypy src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs