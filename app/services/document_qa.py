from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from app.config.index import settings
from app.logging.logging import logger
from app.services.vector_store import VectorStore
from app.utils.mysql_client import MySQLClient
from sqlalchemy.orm import Session
from fastapi import HTTPException


class DocumentQA:
    """文档问答核心类"""

    def __init__(self, db: Session):
        self.llm = None
        self.vectorstore = None
        self.mysql = MySQLClient(db)
        self.init_resources()

    def init_resources(self, streaming=False):
        """初始化 LLM 和向量数据库"""
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_API_BASE,
            max_tokens=settings.MAX_TOKENS,
            streaming=streaming,
        )
        self.vectorstore = VectorStore.load_vectorstore()
        logger.info("FAISS 向量数据库已成功加载！")

    def get_memory(self, session_id: str) -> ConversationBufferMemory:
        """获取带历史记录的记忆对象"""
        memory = ConversationBufferMemory(
            input_key="question",
            output_key="answer",
            memory_key="chat_history",
            return_messages=True,
        )

        # 从MySQL加载历史记录
        history = self.mysql.get_chat_history(session_id)
        for msg in history:
            memory.save_context(
                {"question": msg["question"]}, {"answer": msg["answer"]}
            )
        return memory

    def create_qa_chain(self, session_id: str, streaming_handler=None):
        """创建问答链"""
        if streaming_handler:
            self.init_resources(streaming=True)
            self.llm.callbacks = [streaming_handler]

        # 获取带历史记录的记忆对象
        memory = self.get_memory(session_id)

        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            memory=memory,
            return_source_documents=True,
            output_key="answer",
        )

    def save_chat_history(self, session_id: str, question: str, answer: str):
        """保存对话历史到MySQL"""
        self.mysql.save_chat_history(session_id, question, answer)

    def get_chat_history(self, session_id: str):
        """获取聊天历史"""
        # 检查 session_id 是否存在
        history = self.mysql.get_chat_history(session_id)
        if not history:
            raise HTTPException(status_code=404, detail=f"会话 ID {session_id} 不存在")
        return history

    async def check_session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return await self.mysql.exists(session_id)
