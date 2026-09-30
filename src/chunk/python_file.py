import ast
from ast import AST
from .Chunk import Chunk
from .utils import split_evey_n_character


def large_code_chunk(max_chunk_size: int, index: int,  source: str, node: AST, file: str):
    if not isinstance(node, ast.FunctionDef):
        return []
    code = ast.get_source_segment(source, node)
    if code is None:
        return []
    chunks = []
    splitted_code = split_evey_n_character(max_chunk_size, code)
    for i in range(len(splitted_code)):
        content = splitted_code[i]
        first = i * max_chunk_size + index
        last = first + len(content)
        chunks.append(Chunk(file_path=file,first_char_index=first,last_char_index=last, content=content))
    # print(t)
    return chunks

def chunk_python_code(max_chunk_size: int, file: str):
    with open(file, "r") as f:
        source= f.read()
        
    lines = source.splitlines(keepends=True)
    len_lines = [len(line) for line in lines]
    tree = ast.parse(source)

    chunks = []
    index = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.end_lineno is None:
                continue
            content = ast.get_source_segment(source, node)
            index = sum(len_lines[:node.lineno-1])
            if content is None:
                continue
            code_size = len(content)
            if code_size > max_chunk_size:
                chunks += large_code_chunk(max_chunk_size, index, source, node, file)
            else:
                chunks.append(Chunk(file_path=file,content=content, first_char_index=index, last_char_index=index+code_size))
            
            # print(ast.get_source_segment(source, node))
            
    # print(tree)
    return chunks
