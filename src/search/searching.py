"""BM25 search over the indexed chunks."""
import json
from typing import Any
from .Token import Token
import math
from ..models.minimal_source import MinimalSource
from ..models.student_search import MinimalSearchResults
import os
from tqdm import tqdm
from ..utils import remove_stopwords
from ..models.rag_dataset import RagDataset
from ..llm.LLM import LLM


def open_chunks() -> list[dict[str, Any]]:
    """Load the chunks saved in data/processed/index.json.

    Returns:
        The chunks as dictionaries.
    """
    chunks: list[dict[str, Any]] = []
    with open("data/processed/index.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return chunks


def find_index_min(array: list[tuple[int, float]]) -> tuple[int, float]:
    """Find the entry with the lowest score.

    Args:
        array: (chunk index, score) pairs.

    Returns:
        The position of the lowest score in array and that score.
    """
    min_value = float('+inf')
    min_index = 0
    for i in range(len(array)):
        if array[i][1] < min_value:
            min_index = i
            min_value = array[i][1]
    return min_index, min_value


def count_tokens(tokens: list[str]) -> dict[str, int]:
    """Count the occurrences of each distinct token.

    Args:
        tokens: List of tokens.

    Returns:
        A mapping from token to its number of occurrences.
    """
    unique = set(tokens)
    d: dict[str, int] = {}
    for item in unique:
        count = tokens.count(item)
        d[item] = count
    return d


def calculate_BM25(chunks: list[dict[str, Any]],
                   tokenized_quest: list[list[Token]],
                   avg_token_chunks: float,
                   k: int) -> list[list[tuple[int, float]]]:
    """Score every chunk for every question with BM25.

    Uses k1=1 and b=0.5. Only the k best chunks of each question are kept.

    Args:
        chunks: Chunks, each with "tokenized" and "count_list" entries.
        tokenized_quest: Tokens of each question.
        avg_token_chunks: Average number of tokens per chunk.
        k: Number of chunks to keep per question.

    Returns:
        For each question, the (chunk index, score) pairs sorted by
        decreasing score.
    """
    k1 = 1
    b = 0.5
    questions_len = len(tokenized_quest)
    top_k_chunks: list[list[tuple[int, float]]] = [
        [] for _ in range(questions_len)]
    nb_chunks = len(chunks)
    min_index = [0] * questions_len
    min_value = [float('+inf')] * questions_len
    for i_chunk, chunk in tqdm(enumerate(chunks), total=len(chunks)):
        len_chunk = len(chunk["tokenized"])
        for quest_i, quest in enumerate(tokenized_quest):
            score = 0
            for i, token in enumerate(quest):
                IDF = math.log(
                    (nb_chunks + 0.5)
                    / (token.document_frequency + 0.5))
                count = chunk["count_list"][quest_i][i]
                norm = 1 - b + b * (len_chunk / avg_token_chunks)
                score += IDF * (count * (k1 + 1)) / (count + k1 * norm)
            if len(top_k_chunks[quest_i]) < k:
                top_k_chunks[quest_i].append((i_chunk, score))
                min_index[quest_i], min_value[quest_i] = find_index_min(
                    top_k_chunks[quest_i])

            else:
                if score > min_value[quest_i]:
                    top_k_chunks[quest_i][min_index[quest_i]] = (
                        i_chunk, score)
                    min_index[quest_i], min_value[quest_i] = find_index_min(
                        top_k_chunks[quest_i])
            top_k_chunks[quest_i].sort(key=lambda x: x[1], reverse=True)

    return top_k_chunks


def count_tokens_chunks(chunks: list[dict[str, Any]],
                        tokenized_quest: list[list[Token]]) -> float:
    """Count query tokens in each chunk and their document frequency.

    Adds a "count_list" entry to every chunk and increments the
    document_frequency of the tokens (both in place).

    Args:
        chunks: Chunks, each with a "tokenized" entry.
        tokenized_quest: Tokens of each question.

    Returns:
        The average number of tokens per chunk.
    """
    avg_token_chunks = 0
    for chunk in tqdm(chunks, total=len(chunks)):
        avg_token_chunks += len(chunk["tokenized"])
        chunk["count_list"] = []
        tokens_occurence = count_tokens(chunk["tokenized"])
        for tokens in tokenized_quest:
            token_count_list = []
            for token in tokens:
                count = 0
                if token.token in tokens_occurence:
                    count = tokens_occurence[token.token]
                token_count_list.append(count)
                if count > 0:
                    token.document_frequency += 1
            chunk["count_list"].append(token_count_list)
    return avg_token_chunks / len(chunks)


def retrieving(tokenized_questions: list[list[Token]],
               k: int) -> list[list[MinimalSource]]:
    """Find the k best chunks for each question.

    Args:
        tokenized_questions: Tokens of each question.
        k: Number of chunks to retrieve per question.

    Returns:
        For each question, its k best sources, best first.
    """
    chunks = open_chunks()
    avg_token_chunks = count_tokens_chunks(chunks, tokenized_questions)
    top_k_chunks = calculate_BM25(
        chunks, tokenized_questions, avg_token_chunks, k)

    list_top_minimal_source = []
    for top in top_k_chunks:
        minimal_sources = []
        for chunk_info in top:
            chunk = chunks[chunk_info[0]]
            file_path = chunk["file_path"].replace("\\", "/")
            minimal_sources.append(
                MinimalSource(
                    file_path=file_path,
                    first_character_index=chunk["first_char_index"],
                    last_character_index=chunk["last_char_index"]))
        list_top_minimal_source.append(minimal_sources)
    return list_top_minimal_source


def start_searching_dataset(llm: LLM, dataset_path: str,
                            save_directory: str, k: int) -> None:
    """Search the k best chunks for each question of a dataset.

    The results are saved as JSON in save_directory, under the name of the
    dataset file.

    Args:
        llm: LLM whose tokenizer is used.
        dataset_path: Path to the JSON dataset of questions.
        save_directory: Directory where the results are written.
        k: Number of chunks to retrieve per question.

    Returns:
        None.
    """
    with open(dataset_path, "r", encoding='utf-8') as f:
        rag_dataset = RagDataset.model_validate_json(f.read())
    file_name = os.path.basename(dataset_path)
    tokenized_questions = []
    for question in rag_dataset.rag_questions:
        tokens = llm.tokenize(question.question.lower())
        tokens = list(set(tokens))
        tokens = remove_stopwords(tokens)
        # tokens += add_identifiers(question.question)
        list_tokens = []
        for token in tokens:
            list_tokens.append(Token(token))
        tokenized_questions.append(list_tokens)
    print("nb questions:", len(tokenized_questions))

    list_top_minimal_source = retrieving(tokenized_questions, k)

    list_minimal_search_res = []
    for i_quest, question in enumerate(rag_dataset.rag_questions):
        question_text = question.question
        sources = list_top_minimal_source[i_quest]
        minimal_search_res = MinimalSearchResults(
            question_id=question.question_id,
            question=question_text,
            retrieved_sources=sources)
        list_minimal_search_res.append(minimal_search_res)

    os.makedirs(save_directory, exist_ok=True)
    path = os.path.join(save_directory, file_name)
    with open(path, "w", encoding='utf-8') as f:
        results = [result.model_dump() for result in list_minimal_search_res]
        json.dump({"k": k, "search_results": results}, f,
                  indent=2, ensure_ascii=False)
    print("Saved student_search_results to", path)


def start_searching(llm: LLM, query: str, k: int) -> dict[str, Any]:
    """Search the k best chunks for one query and print them.

    Args:
        llm: LLM whose tokenizer is used.
        query: The question.
        k: Number of chunks to retrieve.

    Returns:
        A dictionary with "k", "question" and "retrieved_sources".
    """
    tokenized_query = llm.tokenize(query.lower())
    tokenized_query = remove_stopwords(tokenized_query)
    tokens = [[Token(token) for token in tokenized_query]]

    list_top_minimal_source = retrieving(tokens, k)
    output: dict[str, Any] = {
        "k": k, "question": query, "retrieved_sources": []}
    for min_s in list_top_minimal_source[0]:
        print(f"{min_s.file_path} [{min_s.first_character_index}:"
              f"{min_s.first_character_index}]")
        output["retrieved_sources"].append(min_s.model_dump())

    return output
