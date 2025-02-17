from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
import config
from openai import OpenAI


def init_qa_chain():
    # 初始化 LLM
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        openai_api_key=config.OPENAI_API_KEY,
        openai_api_base=config.OPENAI_API_BASE,
        max_tokens=config.MAX_TOKENS,
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
    llm, vectorstore = init_qa_chain()
    # 构建 QA Chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="map_rerank",
        retriever=vectorstore.as_retriever(),
    )
    response = qa_chain.run(question)
    return response


def query_documents_stream(question: str):
    """流式查询文档并返回答案"""
    # 获取相关文档
    docs = get_relevant_documents(question)
    context = prepare_context(docs)

    # 调用 LLM 进行流式回答
    for chunk in get_streaming_response(context, question):
        yield chunk


def get_streaming_response(context: str, question: str):
    """从 LLM 获取流式回答"""
    client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_API_BASE)

    messages = [
        {"role": "system", "content": f"请基于以下信息回答问题：\n\n{context}"},
        {"role": "user", "content": question},
    ]

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo", messages=messages, stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content


if __name__ == "__main__":
    # 示例查询
    query = "公司全称有哪些"
    answer = query_documents(query)
    print(f"问题：{query}")
    print(f"回答：{answer}")
