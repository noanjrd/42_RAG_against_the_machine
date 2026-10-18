"""Chunking of text and markdown files."""
from .Chunk import Chunk
from ..utils import split_evey_n_character


def chunk_large_text(max_chunk_size: int, file: str, index: int,
                     text: str) -> list[Chunk]:
    """Split an oversized text into fixed-size chunks.

    Args:
        max_chunk_size: Maximum number of characters per chunk.
        file: Path of the file.
        index: Offset of the text in the file.
        text: Text to split.

    Returns:
        The chunks, in order.
    """
    chunks = []
    subtexts = split_evey_n_character(max_chunk_size, text)
    n = len(subtexts)
    for i in range(n):
        content = subtexts[i]
        first = max_chunk_size * i + index
        last = first + min(max_chunk_size, len(content))
        chunks.append(
            Chunk(
                file_path=file,
                content=content,
                first_char_index=first,
                last_char_index=last,
                tokenized=None,
                is_code=False))
    return chunks


def chunk_text(
        max_chunk_size: int,
        file: str,
        text: str,
        split_chars: list[str],
        split_chars_i: int = 0,
        index: int = 0) -> list[Chunk]:
    """Recursively split a text on a list of separators.

    Pieces that fit in max_chunk_size become chunks. Larger pieces are
    split with the next separator, or by fixed size when none is left.

    Args:
        max_chunk_size: Maximum number of characters per chunk.
        file: Path of the file.
        text: Text to split.
        split_chars: Separators, from the coarsest to the finest.
        split_chars_i: Index of the separator currently used.
        index: Offset of text in the file.

    Returns:
        The chunks of the text.
    """
    chunks = []

    subtexts = text.split(split_chars[split_chars_i])
    n = len(subtexts)
    len_subtexts = [len(subtext) for subtext in subtexts]
    for i_sub in range(n):
        current_index = index + \
            sum(len_subtexts[:i_sub]) + len(split_chars[split_chars_i]) * i_sub
        current_para_len = len_subtexts[i_sub]
        if current_para_len > max_chunk_size and split_chars_i >= len(
                split_chars) - 1:
            chunks += chunk_text(max_chunk_size,
                                 file,
                                 subtexts[i_sub],
                                 split_chars,
                                 split_chars_i + 1,
                                 index=current_index)
        elif current_para_len > max_chunk_size:
            chunks += chunk_large_text(max_chunk_size,
                                       file, current_index, subtexts[i_sub])
        else:
            chunks.append(
                Chunk(
                    file_path=file,
                    first_char_index=current_index,
                    last_char_index=current_index +
                    current_para_len,
                    content=subtexts[i_sub],
                    tokenized=None,
                    is_code=False))

    return chunks
