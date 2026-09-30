def split_evey_n_character(max_chunk_size, text):
    n = len(text)
    splitted_text = [text[i: i+max_chunk_size] for i in range(0,n, max_chunk_size)]
    return splitted_text