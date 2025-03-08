from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from app.config.index import settings
from app.logging.logging import logger
from app.core.vector_store import VectorStore
from sqlalchemy.orm import Session


class DocumentQA:
    def __init__(self, db: Session):
        self.llm = None
        self.db = db
        self.vectorstore = None
        self.init_resources()

    def init_resources(self, streaming=False):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_API_BASE,
            max_tokens=settings.MAX_TOKENS,
            streaming=streaming,
        )
        self.vectorstore = VectorStore.load_vectorstore()
        logger.info("FAISS 向量数据库已成功加载！")

    async def get_memory(
        self, session_id: str, user_id: str
    ) -> ConversationBufferMemory:
        memory = ConversationBufferMemory(
            input_key="question",
            output_key="answer",
            memory_key="chat_history",
            return_messages=True,
        )
        from app.services.frontend.index import chat_history_serve

        history = await chat_history_serve(session_id, user_id, self.db)
        for msg in history:
            memory.save_context(
                {"question": msg["question"]}, {"answer": msg["answer"]}
            )
        return memory

    async def create_qa_chain(
        self, session_id: str, streaming_handler=None, user_id: str = None
    ):
        if streaming_handler:
            self.init_resources(streaming=True)
            self.llm.callbacks = [streaming_handler]

        memory = await self.get_memory(session_id, user_id)

        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            memory=memory,
            return_source_documents=True,
            output_key="answer",
        )
