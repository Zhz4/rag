from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), index=True, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ChatHistory(session_id={self.session_id})>"


class sessions(Base):
    __tablename__ = "sessions"

    session_id = Column(String(64), primary_key=True, index=True, nullable=False)
    title = Column(String(64), nullable=False)
    user_id = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False)


class files(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    is_study = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
