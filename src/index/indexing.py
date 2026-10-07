import os
from .Chunk import Chunk 
from .python_file import chunk_python_code
from .text_file import chunk_text
from ..llm.LLM import LLM
from tqdm import tqdm
from pydantic import TypeAdapter
from ..utils import remove_stopwords, add_identifiers
import re


def save_to_json(chunks: list[Chunk]):
    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/index.json", "wb") as f:
        f.write(TypeAdapter(list[Chunk]).dump_json(chunks, indent=2))
        
        
def path_token(path):
    path = path.lower()
    path = os.path.splitext(path)[0]
    return [p for p in re.split(r"[^a-z0-9]+", path) if p]


def tokenize_content(chunks: list[Chunk], llm):
    n_chunks = len(chunks)
    for i in tqdm(range(n_chunks), desc="Tokenizing"):
        chunk = chunks[i]
        content = chunk.content.lower()
        tokenized = llm.tokenize(content)
        tokenized = remove_stopwords(tokenized)
        chunk.tokenized = tokenized
        if chunk.is_code == True:
            tokenized += path_token(chunk.file_path)
            chunk.tokenized += add_identifiers(chunk.content)
    # print(t)

    return


def list_all_files():
    files_list = []
    for root, dirs, files in os.walk("data/raw/vllm-0.10.1"):
        for file in files:
            name, extension = os.path.splitext(file)
            file = os.path.join(root, file)
            file = file.replace("\\", '/')
            if extension in [".md", ".txt", ".py"]:
                files_list.append(file)
    return files_list

def start_indexing(max_chunk_size: int, llm: LLM):
    chunks = []
    print(max_chunk_size)
    files_list = list_all_files()
    n_files = len(files_list)
    print("nb of files:", n_files)
    for i in tqdm(range(n_files), desc="Chunking"):
        file = files_list[i]
        name, extension = os.path.splitext(file)
        if extension == ".py":
            chunks += chunk_python_code(max_chunk_size, file)
        if extension in [".md", ".txt"]:
            with open(file, "r", encoding="utf-8") as f:
                text = f.read()
            if extension == ".txt":
                chunks += chunk_text(max_chunk_size, file, text, ["\n\n", "\n"])
            else:
                chunks += chunk_text(max_chunk_size, file, text, ["\n# ", "\n## ", "\n### ", "\n\n", "\n"])
                    
            # print(file)
    tokenize_content(chunks,llm)
    save_to_json(chunks)
    print(f"Ingestion complete! Indexed {len(chunks)} chunks under data/processed")
    # index_t =3
    # print(chunks[index_t].content,  chunks[index_t].first_char_index, chunks[index_t].last_char_index, chunks[index_t].file_path, chunks[index_t].tokenized)
    return