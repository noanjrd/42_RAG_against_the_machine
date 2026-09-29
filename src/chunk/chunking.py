import os 
import ast
from ast import AST
from .Chunk import Chunk 

def large_code_chunk(max_chunk_size: int, source: str, node: AST, file: str):
    if not isinstance(node, ast.FunctionDef):
        return []
    code = ast.get_source_segment(source, node)
    if code is None:
        return []
    chunks = []
    splitted_code = code.split('\n')
    for i in range(0, len(splitted_code), max_chunk_size):
        last_char_index_temp = min(len(splitted_code), i+max_chunk_size)
        content = '\n'.join(splitted_code[i:last_char_index_temp])
        chunks.append(Chunk(file_path=file,first_char_index=node.lineno + i,last_char_index= node.lineno + i + last_char_index_temp, content=content))
    # print(t)
    return chunks

def chunk_python_code(max_chunk_size: int, file: str):
    with open(file, "r") as f:
        source= f.read()
        
    tree = ast.parse(source)

    chunks = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.end_lineno is None:
                continue
            code_size = node.end_lineno - node.lineno
            if code_size > max_chunk_size:
                chunks += large_code_chunk(max_chunk_size, source, node, file)
            # else:
            #     content = ast.get_source_segment(source, node)
            #     if content is None:
            #         continue
            #     chunks.append(Chunk(file_path=file,content=content, first_char_index=node.lineno, last_char_index=node.end_lineno))
            
            # print(ast.get_source_segment(source, node))
            
    # print(tree)
    return chunks

def going_through_data(max_chunk_size: int):
    print("hey2")
    chunks = []
    for root, dirs, files in os.walk("data/raw/vllm-0.10.1"):
        for file in files:
            name, extension = os.path.splitext(file)
            if extension == ".py":
                chunks += chunk_python_code(max_chunk_size, os.path.join(root, file))
            # print(file)
    print(chunks[0].content,  chunks[0].first_char_index, chunks[0].last_char_index, chunks[0].file_path)
    return