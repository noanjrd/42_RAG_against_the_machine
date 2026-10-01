import os 
import ast
from ast import AST
from .Chunk import Chunk 
from .python_file import chunk_python_code
from .text_file import chunk_text
from ..llm.model import LLM
from tqdm import tqdm
from pydantic import TypeAdapter
import json

def save_to_json(chunks: list[Chunk]):
    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/index.json", "wb") as f:
        f.write(TypeAdapter(list[Chunk]).dump_json(chunks, indent=2))
        
        
    

def tokenize_content(chunks: list[Chunk], llm):
    n_chunks = len(chunks)
    for i in tqdm(range(n_chunks)):
        chunk = chunks[i]
        chunk.tokenized = llm.tokenize(chunk.content)
    # print(t)
    return


def list_all_files():
    files_list = []
    for root, dirs, files in os.walk("data/raw/vllm-0.10.1"):
        for file in files:
            name, extension = os.path.splitext(file)
            file = os.path.join(root, file)
            if extension in [".md", ".txt", ".py"]:
                files_list.append(file)
    return files_list

def start_indexing(max_chunk_size: int, llm: LLM):
    print("hey2")
    chunks = []
    print(max_chunk_size)
    files_list = list_all_files()
    n_files = len(files_list)
    print("nb of files:", n_files)
    for i in tqdm(range(n_files)):
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
    index_t =3
    tokenize_content(chunks,llm)
    save_to_json(chunks)
    print(f"Ingestion complete! Indexed {len(chunks)} chunks under data/processed")
    print(chunks[index_t].content,  chunks[index_t].first_char_index, chunks[index_t].last_char_index, chunks[index_t].file_path, chunks[index_t].tokenized)
    return