from pydantic import BaseModel
from typing import List

from .questions import AnsweredQuestion, UnansweredQuestion


class RagDataset(BaseModel):
    rag_questions: List[AnsweredQuestion | UnansweredQuestion]
