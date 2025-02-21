from pydantic import BaseModel


class Question(BaseModel):
    text: str
    session_id: str


class Answer(BaseModel):
    question: str
    answer: str
