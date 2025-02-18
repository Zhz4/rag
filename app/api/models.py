from pydantic import BaseModel

class Question(BaseModel):
    text: str

class Answer(BaseModel):
    question: str
    answer: str 