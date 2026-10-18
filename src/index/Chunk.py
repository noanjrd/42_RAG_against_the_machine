"""Data model of an indexed chunk."""
from pydantic import BaseModel


class Chunk(BaseModel):
    """A piece of a source file stored in the index.

    Attributes:
        file_path: File the chunk comes from.
        content: Text of the chunk.
        first_char_index: Start offset of the chunk in the file.
        last_char_index: End offset (exclusive) of the chunk in the file.
        tokenized: Tokens used for the search, None until tokenized.
        is_code: True for Python code chunks, False for text.
    """
    file_path: str
    content: str
    first_char_index: int
    last_char_index: int
    tokenized: None | list[str]
    is_code: bool
