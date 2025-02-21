from pydantic import BaseModel
from typing import Optional


class Question(BaseModel):
    text: str
    session_id: Optional[str] = None


class Answer(BaseModel):
    question: str
    answer: str
