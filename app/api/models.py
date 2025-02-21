from pydantic import BaseModel


class Question(BaseModel):
    text: str
    session_id: str  # 用于标识会话


class Answer(BaseModel):
    question: str
    answer: str
