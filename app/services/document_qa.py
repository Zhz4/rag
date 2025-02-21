from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from app.core.config import settings
from app.core.logging import logger
from app.services.vector_store import VectorStore
from app.utils.redis_client import RedisClient


class DocumentQA:
    """文档问答核心类"""

    def __init__(self):
        self.llm = None
        self.vectorstore = None
        self.redis = RedisClient()
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

        # 从Redis加载历史记录
        history = self.redis.get_chat_history(session_id)
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
        """保存对话历史到Redis"""
        history = self.redis.get_chat_history(session_id)
        history.append({"question": question, "answer": answer})
        self.redis.save_chat_history(session_id, history)

    async def check_session_exists(self, session_id: str) -> bool:
        """
        检查会话是否存在

        Args:
            session_id: 会话ID

        Returns:
            bool: 会话是否存在
        """
        key = f"chat_history:{session_id}"
        exists = await self.redis.exists(key)
        return exists
