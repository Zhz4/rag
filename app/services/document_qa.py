from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from app.core.config import settings
from app.core.logging import logger
from app.services.vector_store import VectorStore


class DocumentQA:
    """文档问答核心类"""

    def __init__(self):
        self.llm = None
        self.vectorstore = None
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

    def create_qa_chain(self, streaming_handler=None):
        """创建问答链"""
        if streaming_handler:
            self.init_resources(streaming=True)
            self.llm.callbacks = [streaming_handler]

        memory = ConversationBufferMemory(
            input_key="question",
            output_key="answer",
            memory_key="chat_history",
            return_messages=True,
        )

        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 3}  # 返回前3个最相关的文档
            ),
            memory=memory,
            return_source_documents=True,  # 确保返回源文档
            output_key="answer",
        )
