import json
from .Token import Token
import math
from ..models.minimal_source import MinimalSource
from ..models.student_search import MinimalSearchResults
import os
from pydantic import TypeAdapter
from tqdm import tqdm

def open_chunks():
    chunks = {}
    with open("data/processed/index.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return chunks

def count_tokens_chunks(chunks, tokens: list[Token]):
    
    avg_token_chunks = 0
    for chunk in chunks:
        avg_token_chunks += len(chunk["tokenized"])
        chunk["count_list"] = []
        for token in tokens:
            count = chunk['tokenized'].count(token.token)
            chunk["count_list"].append(count)
            if count > 0:
                token.document_frequency += 1
    # avg_token_doc
    return avg_token_chunks / len(chunks)

def find_index_min(array):
    min_value = float('+inf')
    min_index = 0
    for i in range(len(array)):
        if array[i][1] < min_value:
            min_index = i
            min_value = array[i][1]
    return min_index, min_value

def calculate_BM25(chunks:list[dict], tokens:  list[Token], avg_token_chunks, k):
    k1 = 1.5
    b = 0.75
    top_k_chunks = []
    nb_chunks = len(chunks)
    min_index, min_value = 0, float('+inf')
    for i_chunk, chunk in enumerate(chunks):
        len_chunk = len(chunk["tokenized"])
        score = 0
        for i, token in enumerate(tokens):
            IDF = math.log(
                (nb_chunks - token.document_frequency + 0.5)
                / (token.document_frequency + 0.5))
            count = chunk["count_list"][i]
            score += IDF * (count * (k1 + 1)) / (count + k1 * (1 - b + b * (len_chunk / avg_token_chunks)))
        if len(top_k_chunks) < k:
            top_k_chunks.append((i_chunk, score))
            min_index, min_value = find_index_min(top_k_chunks)
        else:
            if score > min_value:
                top_k_chunks[min_index] = (i_chunk, score)
                min_index, min_value = find_index_min(top_k_chunks)
    
    return top_k_chunks

def start_searching(llm, query: str, k: int):
    tokenized_query = llm.tokenize(query)
    # print("Tokenized query:", tokenized_query)
    chunks = open_chunks()
    tokens = [Token(token) for token in tokenized_query]
    avg_token_chunks = count_tokens_chunks(chunks, tokens)
    top_k_chunks = calculate_BM25(chunks, tokens, avg_token_chunks, k)
    # [print(chunks[top[0]]['content'], '\n\n\n----------------------------------\n\n') for top in top_k_chunks]
    # print(top_k_chunks)
    
    sources = []
    for ch_i, _ in top_k_chunks:
        chunk = chunks[ch_i]
        sources.append(MinimalSource(file_path=chunk["file_path"], first_character_index=chunk["first_char_index"], last_character_index=chunk["last_char_index"]))
    # print(chunks)
    
    return sources


def start_searching_dataset(llm, dataset_path, save_directory , k):
    with open(dataset_path, "r", encoding='utf-8') as f:
        questions = json.load(f)["rag_questions"]
    list_questions = []
    n_questions = len(questions)
    for i in tqdm(range(n_questions)):
        question = questions[i]
        question_text = question["question"]
        sources = start_searching(llm, question_text , k)
        list_questions.append(MinimalSearchResults(question_id=question["question_id"], question=question_text, retrieved_sources=sources))
        
    os.makedirs(save_directory, exist_ok=True)
    path = save_directory + "/StudentSearchResults.json"
    with open(path, "wb") as f:
            f.write(TypeAdapter(list[MinimalSearchResults]).dump_json(list_questions, indent=2))
    return