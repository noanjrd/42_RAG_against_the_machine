*This project has been created as part of the 42 curriculum by njard.*

# RAG against the machine

## Description

A Retrieval-Augmented Generation (RAG) system that answers questions about the [vLLM 0.10.1](https://github.com/vllm-project/vllm) repository, entirely locally and from the command line.

**Goal:** given a question, retrieve the few snippets (file path and character range) of the codebase that answer it, then let a small local model (`Qwen/Qwen3-0.6B`) write an answer grounded in those snippets. Retrieval quality is measured with recall@k.

**Overview:** the pipeline has four stages: indexing (chunk and tokenize the corpus), retrieving (BM25 ranking), augmenting (build the prompt from the best passages) and generating (Qwen3-0.6B writes the answer). Everything is exposed through a Python Fire CLI, with tqdm progress bars on long operations and pydantic models for the data exchanged between stages.

## Instructions

Requirements: Python 3.13+, [uv](https://docs.astral.sh/uv/), about 2.5 GB of free RAM, and network access once to download the Qwen3-0.6B weights (about 1.2 GB, cached afterwards).

```bash
make install                                   # uv sync

# the corpus and datasets are shipped zipped in compressed/
mkdir -p data/raw data/datasets
unzip compressed/vllm-0.10.1.zip -d data/raw
unzip compressed/datasets.zip -d data

uv run python -m src index --max_chunk_size 2000
uv run python -m src search "How to configure the OpenAI server?" --k 5
uv run python -m src search_dataset \
    --dataset_path data/datasets/UnansweredQuestions/dataset_docs_public.json \
    --k 10 --save_directory data/output/search_results/UnansweredQuestions
uv run python -m src answer "how do I enable prefix caching?" --k 5
uv run python -m src answer_dataset \
    --student_search_results_path data/output/search_results/UnansweredQuestions/dataset_docs_public.json \
    --save_directory data/output/search_results_and_answer/UnansweredQuestions
uv run python -m src evaluate \
    --student_search_results_path data/output/search_results/UnansweredQuestions/dataset_docs_public.json \
    --dataset_path data/datasets/AnsweredQuestions/dataset_docs_public.json
```

Makefile rules: `install`, `run`, `debug`, `clean`, `lint` (flake8 and mypy), plus shortcuts for each command (`make index`, `make search_dataset_docs`, `make evaluate_code`, ...).

## System architecture

```
 data/raw/ ──► Chunking ──► Tokenizing ──► data/processed/index.json
                                                   │
 question ──► tokenize (same pipeline) ──► BM25 top-k ──► sources (file, first, last)
                                                   │
                      read the ranges from the original files, merge overlaps
                                                   │
                           prompt + Qwen3-0.6B ──► answer (JSON)
```

| Component | Folder | Role |
|---|---|---|
| Indexer | `src/index/` | Chunks files (code and text strategies), tokenizes chunks, writes the index |
| Searcher | `src/search/` | BM25 scoring; handles one query or a whole dataset in one pass |
| Answerer | `src/answer/` | Rebuilds passages from the original files, builds the prompt |
| LLM wrapper | `src/llm/` | Loads the Qwen3 tokenizer and model, generates the answer |
| Models | `src/models/` | Pydantic models (`MinimalSource`, `UnansweredQuestion`, `AnsweredQuestion`, `RagDataset`, `MinimalSearchResults`, `MinimalAnswer`, `StudentSearchResults`, `StudentSearchResultsAndAnswer`) |
| Evaluation | `src/evaluation/` | Own recall@k computation (IoU >= 0.05) |
| CLI | `src/__main__.py` | Fire entry point |

The same tokenization is used for chunks and queries so their tokens match.

## Chunking strategy

Every chunk stores its file path, its `first_char_index` / `last_char_index` in the original file and whether it is code. No chunk exceeds `--max_chunk_size` (default 2000 characters).

- **Python files:** parsed with `ast`; each function is one chunk. A function longer than the limit is cut into fixed-size pieces.
- **Markdown / text files:** split recursively on separators from coarse to fine (`\n# `, `\n## `, `\n### `, `\n\n`, `\n`). A piece that is still too long after the last separator is cut into fixed-size pieces.

Character offsets always refer to the original file, so any source can be recovered with `text[first:last]`.

## Retrieval method

- **Tokenization:** lowercase, Qwen3 tokenizer, English stopwords removed. For code chunks the full identifiers (`max_model_len`) and their parts (`max`, `model`, `len`) are both kept, so a question can match either a paraphrase or a verbatim identifier. The words of the file path are added to every chunk.
- **Ranking:** BM25 implemented from scratch with `k1 = 1` and `b = 0.5`. The index is scanned once and the top-k chunks of every question are kept simultaneously, so a whole dataset is scored in a single pass.
- Exactly `k` sources are always returned.

## Performance analysis

Recall@5 on the public datasets (moulinette-style metric, IoU >= 0.05):

| Dataset | Questions | Recall@5 | Required |
|---|---|---|---|
| Documentation | 100 | 82% | 80% |
| Code | 99 | 52% | 50% |

Both thresholds are met, the code score narrowly. Indexing and retrieval times were checked against the limits (5 minutes for indexing, 90 seconds for 200 questions). These scores come from the public questions the pipeline was tuned on, so a hidden set may score slightly lower. Smaller `--max_chunk_size` values give more precise chunks but split context across more of them; 2000 is the default used for the reported scores.

## Design decisions

- **BM25 over TF-IDF:** term-frequency saturation and length normalization suit chunks of very different sizes. Parameters were tuned empirically on the public datasets.
- **One chunk per function for code:** a function is a natural unit that answers a question on its own.
- **Identifier splitting and path words:** questions paraphrase while code quotes identifiers; indexing both forms and the file path widens what can match.
- **Qwen3 tokenizer for indexing:** one tokenizer shared with the generation model, no extra dependency.
- **Answer generation:** thinking mode disabled, answers capped at 75 new tokens, and a system message restricting the model to the provided documentation (and to say so when it does not know). Retrieved ranges are merged when they touch or overlap to save context.
- **Robustness:** degenerate inputs (empty query, `k=0`, missing files, malformed JSON, search before indexing) are handled with clear messages instead of tracebacks.

## Challenges faced

- **Code recall:** only indexing functions leaves out classes, constants and module-level code. Identifier splitting and path words raised code recall above the threshold; indexing whole files is the next step.
- **Exact paths and spans:** the grader compares `file_path` verbatim and uses character overlap, so chunk offsets had to be tracked exactly through recursive splitting.
- **Small model:** Qwen3-0.6B gives short and sometimes wrong answers, and is slow on CPU. A restrictive system prompt, no thinking mode and a token cap keep answers focused and runtime reasonable.
- **Speed:** scoring all questions of a dataset in a single pass over the index keeps retrieval well under the time limit.

## Example usage

```bash
$ uv run python -m src search "How to configure the OpenAI server?" --k 3
data/raw/vllm-0.10.1/docs/serving/openai_compatible_server.md [9867:10100]
data/raw/vllm-0.10.1/vllm/entrypoints/openai/api_server.py [267:400]
...

$ ./moulinette evaluate_student_search_results \
    data/output/search_results/UnansweredQuestions/dataset_docs_public.json \
    data/datasets/AnsweredQuestions/dataset_docs_public.json \
    --k 10 --max_context_length 2000
```

(The paths above are illustrative; run the commands to see your own output.)

## Resources

- [vLLM documentation](https://docs.vllm.ai/)
- [Qwen3 model card](https://huggingface.co/Qwen/Qwen3-0.6B)
- [Robertson & Zaragoza, *The Probabilistic Relevance Framework: BM25 and Beyond*](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf)
- [Introduction to Information Retrieval (Manning et al.)](https://nlp.stanford.edu/IR-book/)
- [Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*](https://arxiv.org/abs/2005.11401)
- [Python Fire](https://github.com/google/python-fire), [pydantic](https://docs.pydantic.dev/), [uv](https://docs.astral.sh/uv/), [Hugging Face Transformers](https://huggingface.co/docs/transformers)

**Use of AI:** AI assistants were used for explanations of RAG and BM25 concepts, for reviewing code and for drafting and polishing documentation (including this README). The design, chunking and retrieval logic were written and tuned by the author, and every AI suggestion was reviewed and tested before being kept.
