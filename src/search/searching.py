import json
from .Token import Token
import math
from ..models.minimal_source import MinimalSource
from ..models.student_search import MinimalSearchResults
import os
from pydantic import TypeAdapter
from tqdm import tqdm
from ..utils import remove_stopwords, add_identifiers
from ..models.questions import UnansweredQuestion
from ..models.rag_dataset import RagDataset


def open_chunks():
    chunks = {}
    with open("data/processed/index.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return chunks


def find_index_min(array):
    min_value = float('+inf')
    min_index = 0
    for i in range(len(array)):
        if array[i][1] < min_value:
            min_index = i
            min_value = array[i][1]
    return min_index, min_value


def count_tokens(tokens):
    unique = set(tokens)
    d = {}
    for item in unique:
        count = tokens.count(item)
        d[item] = count
    return d


def calculate_BM25(chunks:list[dict], tokenized_quest:  list[list[Token]], avg_token_chunks, k):
    k1 = 1
    b = 0.5
    questions_len = len(tokenized_quest)
    top_k_chunks = [[] for _ in range(questions_len)]
    nb_chunks = len(chunks)
    min_index = [0] * questions_len
    min_value = [float('+inf')] * questions_len
    for i_chunk, chunk in tqdm(enumerate(chunks), total=len(chunks)):
        len_chunk = len(chunk["tokenized"])
        for quest_i, quest in enumerate(tokenized_quest):
            score = 0
            for i, token in enumerate(quest):
                IDF = math.log(
                    1 + (nb_chunks - token.document_frequency + 0.5)
                    / (token.document_frequency + 0.5))
                count = chunk["count_list"][quest_i][i]
                score += IDF * (count * (k1 + 1)) / (count + k1 * (1 - b + b * (len_chunk / avg_token_chunks)))
            if len(top_k_chunks[quest_i]) < k:
                top_k_chunks[quest_i].append((i_chunk, score))
                min_index[quest_i], min_value[quest_i] = find_index_min(top_k_chunks[quest_i])

            else:
                if score > min_value[quest_i]:
                    top_k_chunks[quest_i][min_index[quest_i]] = (i_chunk, score)
                    min_index[quest_i], min_value[quest_i] = find_index_min(top_k_chunks[quest_i])
            top_k_chunks[quest_i].sort(key=lambda x: x[1], reverse=True)

    
    return top_k_chunks


def count_tokens_chunks(chunks, tokenized_quest: list[list[Token]]):
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


def retrieving(tokenized_questions, k) -> list[list[MinimalSource]]:
    chunks = open_chunks()
    avg_token_chunks = count_tokens_chunks(chunks, tokenized_questions)
    top_k_chunks = calculate_BM25(chunks, tokenized_questions, avg_token_chunks, k)
    
    list_top_minimal_source= []
    for top in top_k_chunks:
        minimal_sources = []
        for chunk_info in top:
            chunk = chunks[chunk_info[0]]
            file_path = chunk["file_path"].replace("\\", "/")
            minimal_sources.append(MinimalSource(file_path=file_path, first_character_index=chunk["first_char_index"], last_character_index=chunk["last_char_index"]))
        list_top_minimal_source.append(minimal_sources)
    return list_top_minimal_source


def start_searching_dataset(llm, dataset_path, save_directory , k):
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
        minimal_search_res = MinimalSearchResults(question_id=question.question_id, question=question_text, retrieved_sources=sources)
        list_minimal_search_res.append(minimal_search_res)
        
    os.makedirs(save_directory, exist_ok=True)
    path = os.path.join(save_directory, file_name)
    with open(path, "w", encoding='utf-8') as f:
        json.dump({"k": k, "search_results": [result.model_dump() for result in list_minimal_search_res]},f, indent=2, ensure_ascii=False)
    print("Saved student_search_results to", path)


def start_searching(llm, query: str, k: int):
    tokenized_query = llm.tokenize(query.lower())
    tokenized_query = remove_stopwords(tokenized_query)
    tokens = [[Token(token) for token in tokenized_query]]
    
    list_top_minimal_source = retrieving(tokens, k)
    output = {"k": k, "question": query, "retrieved_sources": []}
    for min_s  in list_top_minimal_source[0]:
        print(f"{min_s.file_path} [{min_s.first_character_index}:{min_s.first_character_index}]")
        output["retrieved_sources"].append(min_s.model_dump())

    return output