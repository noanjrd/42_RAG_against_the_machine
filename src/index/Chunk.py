from pydantic import BaseModel


class Chunk(BaseModel):
    file_path: str
    content: str
    first_char_index: int
    last_char_index: int
    tokenized: None | list[str]
    is_code: bool
