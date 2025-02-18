from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
import config
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import json
from langchain.callbacks.base import BaseCallbackHandler
import asyncio


def init_qa_chain(streaming=False):
    # 初始化 LLM
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        openai_api_key=config.OPENAI_API_KEY,
        openai_api_base=config.OPENAI_API_BASE,
        max_tokens=config.MAX_TOKENS,
        streaming=streaming,
        callbacks=[StreamingStdOutCallbackHandler()] if streaming else None,
    )

    # 初始化 Embeddings
    embedding = OpenAIEmbeddings(
        openai_api_key=config.OPENAI_API_KEY,
        openai_api_base=config.OPENAI_API_BASE,
    )

    # 加载向量数据库
    vectorstore = FAISS.load_local(
        config.FAISS_INDEX_PATH, embedding, allow_dangerous_deserialization=True
    )
    print("✅ FAISS 向量数据库已成功加载！")

    return llm, vectorstore


def get_relevant_documents(question: str, k: int = 3):
    """获取与问题相关的文档"""
    _, vectorstore = init_qa_chain()
    docs = vectorstore.similarity_search(question, k=k)
    return docs


def prepare_context(docs) -> str:
    """将文档转换为上下文字符串"""
    return "\n\n".join([doc.page_content for doc in docs])


def query_documents(question: str):
    llm, vectorstore = init_qa_chain(streaming=True)
    # 构建 QA Chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="map_rerank",
        retriever=vectorstore.as_retriever(),
    )
    response = qa_chain.run(question)
    return response


def query_documents_stream(question: str):
    """使用 ConversationalRetrievalChain 进行流式传输"""
    llm, vectorstore = init_qa_chain(streaming=True)

    memory = ConversationBufferMemory(
        input_key="question",
        output_key="answer",
        memory_key="chat_history",
        return_messages=True,
    )
    retriever = vectorstore.as_retriever()

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,  # 让返回的结果包含原始文档
        output_key="answer",
    )

    # 修改查询方式，只获取答案部分
    result = qa_chain.invoke({"question": question})
    if isinstance(result, dict) and "answer" in result:
        yield result["answer"]
    else:
        yield result


class StreamingHandler(BaseCallbackHandler):
    """处理流式输出的回调处理器"""

    def __init__(self):
        self.tokens = []
        self.queue = asyncio.Queue()  # 用于存储token的队列

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """每当有新的token时被调用"""
        await self.queue.put(token)


async def query_documents_stream_for_api(question: str):
    """专门用于 API 的流式传输方法，返回符合 SSE 格式的响应"""
    handler = StreamingHandler()

    llm, vectorstore = init_qa_chain(streaming=True)
    llm.callbacks = [handler]  # 设置流式处理器

    memory = ConversationBufferMemory(
        input_key="question",
        output_key="answer",
        memory_key="chat_history",
        return_messages=True,
    )
    retriever = vectorstore.as_retriever()

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        output_key="answer",
    )

    # 创建一个任务来运行 qa_chain
    task = asyncio.create_task(qa_chain.ainvoke({"question": question}))

    # 持续从队列中获取新的 token
    while True:
        try:
            # 等待新的 token，但设置超时
            token = await asyncio.wait_for(handler.queue.get(), timeout=0.1)
            yield f"data: {json.dumps({'choices': [{'delta': {'content': token}}]}, ensure_ascii=False)}\n\n"
        except asyncio.TimeoutError:
            # 检查 qa_chain 是否完成
            if task.done():
                break
            continue
        except Exception as e:
            print(f"Error: {e}")
            break

    # 发送完成标记
    yield f"data: {json.dumps({'choices': [{'delta': {'content': None}}]}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"
