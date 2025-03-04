from pydantic import BaseModel
from typing import List


class Question(BaseModel):
    text: str
    session_id: str
    user_id: str


class Answer(BaseModel):
    question: str
    answer: str

class DeleteDocumentsRequest(BaseModel):
    file_paths: List[str]
