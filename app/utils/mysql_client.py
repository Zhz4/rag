from sqlalchemy.orm import Session
from app.db.models.chat import ChatHistory, sessions
from typing import List, Dict


class MySQLClient:
    def __init__(self, db: Session):
        self.db = db

    async def get_chat_history(self, session_id: str = None, user_id: str = None):
        """获取会话历史记录

        Args:
            session_id: 会话ID
            user_id: 用户ID
        """
        query = self.db.query(ChatHistory, sessions).join(
            sessions, ChatHistory.session_id == sessions.session_id
        )

        if session_id:
            query = query.filter(ChatHistory.session_id == session_id)
        if user_id:
            query = query.filter(sessions.user_id == user_id)

        results = query.all()

        # 将查询结果转换为字典列表
        history = []
        for chat_history, session in results:
            history.append(
                {
                    "question": chat_history.question,
                    "answer": chat_history.answer,
                    "session_id": chat_history.session_id,
                    "created_at": chat_history.created_at.isoformat(),
                }
            )

        return history

    async def save_chat_history(
        self, session_id: str, question: str, answer: str, user_id: str
    ):
        """保存会话记录"""
        # 检查会话是否存在
        if not await self.exists(session_id, user_id):
            # 创建会话，使用问题的前20个字符作为标题
            title = question[:20] + "..." if len(question) > 20 else question
            session = sessions(
                session_id=session_id,
                user_id=user_id,
                title=title,  # 添加标题
                is_deleted=False,
            )
            self.db.add(session)
            self.db.commit()

        # 保存会话记录
        chat = ChatHistory(session_id=session_id, question=question, answer=answer)
        self.db.add(chat)
        self.db.commit()

    async def exists(self, session_id: str, user_id: str) -> bool:
        """检查会话是否存在"""
        count = (
            self.db.query(sessions)
            .filter(sessions.session_id == session_id, sessions.user_id == user_id)
            .count()
        )
        return count > 0

    async def get_session(self, user_id: str):
        """获取会话列表"""
        results = (
            self.db.query(
                sessions.session_id.label("session_id"),
                sessions.user_id.label("user_id"),
                sessions.title.label("title"),
                sessions.created_at.label("created_at"),
            )
            .filter(sessions.user_id == user_id, sessions.is_deleted == False)
            .order_by(sessions.created_at.desc())
            .all()
        )

        return [row._asdict() for row in results]
