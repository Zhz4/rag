from sqlalchemy.orm import Session
from app.models.chat import ChatHistory
from typing import List, Dict
from datetime import datetime


class MySQLClient:
    def __init__(self, db: Session):
        self.db = db

    def get_chat_history(self, session_id: str) -> List[Dict]:
        """获取会话历史记录"""
        history = (
            self.db.query(ChatHistory)
            .filter(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.created_at)
            .all()
        )

        return [{"question": h.question, "answer": h.answer} for h in history]

    def save_chat_history(self, session_id: str, question: str, answer: str):
        """保存会话记录"""
        chat = ChatHistory(session_id=session_id, question=question, answer=answer)
        self.db.add(chat)
        self.db.commit()

    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        count = (
            self.db.query(ChatHistory)
            .filter(ChatHistory.session_id == session_id)
            .count()
        )
        return count > 0
