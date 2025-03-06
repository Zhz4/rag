from sqlalchemy.orm import Session
from app.db.models.chat import ChatHistory, sessions, Quote
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
        query = (
            self.db.query(ChatHistory, sessions, Quote)
            .join(sessions, ChatHistory.session_id == sessions.session_id)
            .join(
                Quote,
                ChatHistory.id == Quote.chat_history_id,
                isouter=True,  # 使用左连接，因为可能没有引用
            )
        )

        if session_id:
            query = query.filter(ChatHistory.session_id == session_id)
        if user_id:
            query = query.filter(sessions.user_id == user_id)

        results = query.all()

        # 将查询结果转换为字典列表
        history = []
        current_chat = None
        for chat_history, session, quote in results:
            # 如果是新的聊天记录或第一条记录
            if current_chat is None or current_chat["id"] != chat_history.id:
                current_chat = {
                    "id": chat_history.id,
                    "question": chat_history.question,
                    "answer": chat_history.answer,
                    "session_id": chat_history.session_id,
                    "created_at": chat_history.created_at.isoformat(),
                    "quotes": [],
                }
                history.append(current_chat)

            # 如果存在引用，添加到当前聊天记录的quotes列表中
            if quote:
                current_chat["quotes"].append(
                    {
                        "content": quote.content,
                        "page_number": quote.page_number,
                        "source": quote.source,
                    }
                )

        return history

    async def save_chat_history(
        self, session_id: str, question: str, answer: str, user_id: str, sources: list
    ):
        """保存会话记录"""
        try:
            # 检查会话是否存在
            if not await self.exists(session_id, user_id):
                # 创建会话，使用问题的前20个字符作为标题
                title = question[:20] + "..." if len(question) > 20 else question
                session = sessions(
                    session_id=session_id,
                    user_id=user_id,
                    title=title,
                    is_deleted=False,
                )
                self.db.add(session)
                self.db.commit()

            # 先创建会话记录
            chat = ChatHistory(session_id=session_id, question=question, answer=answer)
            self.db.add(chat)
            self.db.commit()
            self.db.refresh(chat)  # 刷新以获取新插入记录的ID

            # 再保存引用
            for source in sources:
                quote = Quote(
                    chat_history_id=chat.id,  # 使用刚创建的chat_history的ID
                    content=source["page_content"],
                    page_number=source["page"],
                    source=source["source"],
                )
                self.db.add(quote)

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

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
