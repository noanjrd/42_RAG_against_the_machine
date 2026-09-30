import os 
import ast
from ast import AST
from .Chunk import Chunk 
from .python_file import chunk_python_code
from .utils import split_evey_n_character



def chunk_large_text(max_chunk_size, file, index, text):
    chunks = []
    subtexts = split_evey_n_character(max_chunk_size, text)
    n = len(subtexts)
    for i in range(n):
        content = subtexts[i]
        first = max_chunk_size * i + index
        last = first  + min(max_chunk_size, len(content))
        chunks.append(Chunk(file_path=file, content=content, first_char_index=first, last_char_index=last))
    return chunks

def chunk_text(max_chunk_size: int,file, text, split_char, index=0):
    chunks = []

    subtexts = text.split(split_char)
    n = len(subtexts)
    len_subtexts = [len(subtext) for subtext in subtexts]
    for i_sub in range(n):
        index = sum(len_subtexts[:i_sub]) + len(split_char) * i_sub
        current_para_len =  len_subtexts[i_sub] 
        if current_para_len > max_chunk_size and len(split_char) > 1:
            chunks += chunk_text(max_chunk_size, file, subtexts[i_sub], split_char[:-1], index=index)
        elif current_para_len > max_chunk_size and len(split_char) <= 1:
            chunks += chunk_large_text(max_chunk_size, file, index, subtexts[i_sub])
        else:
            chunks.append(Chunk(file_path=file, first_char_index=index, last_char_index=index+current_para_len, content=subtexts[i_sub]))
            
            
    
    return chunks



def going_through_data(max_chunk_size: int):
    print("hey2")
    chunks = []
    for root, dirs, files in os.walk("data/raw/vllm-0.10.1"):
        for file in files:
            name, extension = os.path.splitext(file)
            file = os.path.join(root, file)
            # if extension == ".py":
            #     chunks += chunk_python_code(max_chunk_size, os.path.join(root, file))
            if extension == ".txt":
                with open(file, "r") as f:
                    text = f.read()
                chunks += chunk_text(max_chunk_size, file, text, "\n\n")
            # print(file)
    index_t = 1
    print(chunks[index_t].content,  chunks[index_t].first_char_index, chunks[index_t].last_char_index, chunks[index_t].file_path)
    return