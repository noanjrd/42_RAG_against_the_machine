# RAG against the machine

A small retrieval-augmented generation (RAG) system over the [vLLM 0.10.1](https://github.com/vllm-project/vllm) repository.

It answers questions about vLLM's documentation and source code, entirely on your machine and from the command line.

```
 ┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
 │  INDEXING  │ ──► │ RETRIEVING │ ──► │ AUGMENTING │ ──► │ GENERATING │
 └────────────┘     └────────────┘     └────────────┘     └────────────┘
  chunk and          rank the           put the best       the LLM writes
  tokenize the       chunks against     passages and the   the answer from
  repository         the question      question in a      those passages
                     (BM25)             prompt
```

| Stage | What happens | Command |
|---|---|---|
| **Indexing** | Split the repository's files into chunks and tokenize them | `index` |
| **Retrieving** | Rank the chunks against the question with BM25, implemented from scratch | `search`, `search_dataset` |
| **Augmenting** | Read the best passages from the original files and add them to the prompt with the question | `answer`, `answer_dataset` |
| **Generating** | A local LLM (`Qwen/Qwen3-0.6B`) writes the answer, using only those passages | `answer`, `answer_dataset` |

Retrieval is purely lexical, so no embedding model is needed.

## Requirements

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/)
- About 2.5 GB of free RAM (the model is loaded in float32, which is faster on CPU)
- Network access **once**, to download the Qwen3-0.6B weights (about 1.2 GB, cached afterwards)

Python dependencies (`fire`, `pydantic`, `torch`, `tqdm`, `transformers`) are declared in [pyproject.toml](pyproject.toml).

## Installation

```bash
make install        # same as: uv sync
```

## Data layout

| Path | Content |
|---|---|
| `data/raw/vllm-0.10.1/` | The vLLM repository to index (from `downloads/vllm-0.10.1.zip`) |
| `downloads/datasets_public/` | The question datasets: `AnsweredQuestions/` and `UnansweredQuestions/`, each with a docs file and a code file |
| `data/processed/index.json` | The index, written by `index` and read by `search` and `answer` |
| `data/output/` | Search and answer results |


## Usage

The command line is built with [Fire](https://github.com/google/python-fire). Every command has this form:

```bash
uv run 42-rag-against-the-machine <command> [arguments]
```

### `index`

Chunk and tokenize the corpus, then write `data/processed/index.json`.

| Option | Default | Meaning |
|---|---|---|
| `--max_chunk_size` | `2000` | Maximum chunk length in characters |

```bash
uv run 42-rag-against-the-machine index --max_chunk_size=2000
```

Run it again whenever you change the chunking or the tokenization.

### `search`

Find the best passages for **one** question and print them as `file [first:last]`.

| Option | Default | Meaning |
|---|---|---|
| `"<question>"` | required | The question, as a single quoted argument |
| `--k` | `5` | Number of passages to return |

```bash
uv run 42-rag-against-the-machine search "where will i be able to see the benchmark results" --k 10
```

### `search_dataset`

Run the search for **every question** of a dataset and save the results.

| Option | Default | Meaning |
|---|---|---|
| `--dataset_path` | required | Dataset JSON file |
| `--save_directory` | `data/answers` | Where the result file is written |
| `--k` | `5` | Number of passages per question |

```bash
uv run 42-rag-against-the-machine search_dataset \
    --dataset_path downloads/datasets_public/UnansweredQuestions/dataset_docs_public.json \
    --save_directory data/output/search_results/UnansweredQuestions \
    --k 10
```

### `answer`

Search, then generate an answer from the retrieved passages.

| Option | Default | Meaning |
|---|---|---|
| `"<question>"` | required | The question, as a single quoted argument |
| `--k` | `5` | Number of passages given to the model |

```bash
uv run 42-rag-against-the-machine answer "how do I enable prefix caching?" --k 5
```

### `answer_dataset`

Generate an answer for **every question** of a saved search-results file.

| Option | Default | Meaning |
|---|---|---|
| `--student_search_results_path` | required | File written by `search_dataset` |
| `--save_directory` | required | Where the result file is written |

```bash
uv run 42-rag-against-the-machine answer_dataset \
    --student_search_results_path data/output/search_results/UnansweredQuestions/dataset_docs_public.json \
    --save_directory data/output/search_results_and_answer/UnansweredQuestions
```

> **Note:** pass `--k` after the command name. The `Rag` class constructor takes no arguments, so Fire hands the flag to the command.

### Makefile shortcuts

| Target | Runs |
|---|---|
| `make install` | `uv sync` |
| `make index` | `index` |
| `make search` | `search` with a sample question and `--k 10` |
| `make search_dataset_doc` | `search_dataset` on the docs dataset |
| `make search_dataset_code` | `search_dataset` on the code dataset |
| `make answer` | `answer` with a sample question |
| `make answer_dataset_doc` | `answer_dataset` on the docs results |
| `make run ARGS="..."` | Any command, with your own arguments |
| `make lint` | `flake8` and `mypy` |

### Output format

`search_dataset` writes one JSON file, named after the input dataset:

```json
{
  "k": 5,
  "search_results": [
    {
      "question_id": "…",
      "question": "…",
      "retrieved_sources": [
        {
          "file_path": "data/raw/vllm-0.10.1/docs/…",
          "first_character_index": 0,
          "last_character_index": 1200
        }
      ]
    }
  ]
}
```

- `answer_dataset` writes the same structure, with an extra `"answer"` field on each result.
- The character indices refer to the **original file**, so a source can always be recovered with `text[first:last]`.


## How it works

### 1. Chunking (`src/index`)

Each chunk stores its file, its `first_char_index` and `last_char_index` in the original file, its text, and whether it is code.

| File type | Strategy |
|---|---|
| `.py` | Parsed with `ast`; **each function is one chunk**. A function longer than `max_chunk_size` is cut into fixed-size pieces |
| `.md`, `.txt` | Split recursively on separators, from coarse to fine: `\n# `, `\n## `, `\n### `, `\n\n`, `\n`. A piece still too long after the last separator is cut into fixed-size pieces |

### 2. Tokenization (`src/utils.py`, `src/index/indexing.py`)

Chunks and queries go through the same pipeline, so their tokens match:

1. Lowercase, then tokenize with the Qwen3 tokenizer.
2. Remove English stopwords and the tokenizer's space marker.
3. For **code** chunks, also add the full identifiers (`max_model_len`) and their parts (`max`, `model`, `len`).
4. Add the words of the file path (for example `engine`, `arg`, `utils`) to every chunk.

### 3. Retrieval (`src/search`)

- Chunks are ranked with **BM25**, with `k1 = 1` and `b = 0.5` (set in `calculate_BM25`).
- The index is scanned once, and the top `k` chunks are kept for every question at the same time, so a whole dataset is scored in a single pass.
- Exactly `k` passages are always returned. Dropping the ones whose score is far below the others would filter out weak matches, but the subject does not allow it.

### 4. Answering (`src/answer`, `src/llm`)

1. The retrieved ranges are read back from the original files, sorted by file and position, and merged when they touch or overlap.
2. The passages and the question go to Qwen3-0.6B through its chat template.
3. A system message tells the model to answer only from the documentation, and to say so when it cannot.
4. Thinking mode is disabled, and the answer is capped at 75 new tokens.


## Evaluation

The project ships with a `moulinette` binary. It is a Linux program, so run it on Linux or in WSL.

```bash
./moulinette evaluate_student_search_results \
    data/output/search_results/UnansweredQuestions/dataset_docs_public.json \
    data/datasets/AnsweredQuestions/dataset_docs_public.json \
    --k 5 --max_context_length 2000
```

It reports Recall@1, @3, @5 and @10. Run the search with `--k 10` to get a meaningful Recall@10.

### Results

| Dataset | Questions | Recall@5 |
|---|---|---|
| Documentation (public) | 100 | **82%** |
| Code (public) | 99 | **52%** |

The code score is the weaker one, and improving it is the next goal (see [Future improvements](#future-improvements)). These scores come from the public questions the pipeline was tuned on, so a hidden set may score a little lower.


## Project structure

```
src/
├── __main__.py        Command line (Fire) entry point
├── utils.py           Stopwords and identifier extraction
├── index/             Chunking, tokenization, index writing
├── search/            BM25 search over the index
├── answer/            Prompt building and answer generation
├── llm/LLM.py         Qwen3 tokenizer and model wrapper
└── models/            Pydantic models for questions, sources and results
```

## Known limitations

- **Lexical search.** A question that shares no words with its answer will not be found.
- **Small model.** The 0.6B model runs on CPU, so answering a whole dataset is slow, and its answers are short and sometimes wrong.

## Future improvements

- **Python coverage.** Index the whole file, not only functions: classes, dataclass fields, module-level constants, imports and `async def`. This would make the missing code answers reachable.
- **Embeddings.** Add a small sentence-embedding model next to BM25 and merge the two rankings (for example with reciprocal rank fusion). It would find passages that answer a question without sharing its words.
