from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
import config

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
        config.FAISS_INDEX_PATH, 
        embedding, 
        allow_dangerous_deserialization=True
    )
    print("✅ FAISS 向量数据库已成功加载！")

    # 构建 QA Chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="map_rerank",
        retriever=vectorstore.as_retriever(),
    )
    
    return qa_chain

def query_documents(question: str):
    qa_chain = init_qa_chain()
    response = qa_chain.run(question)
    return response

if __name__ == "__main__":
    # 示例查询
    query = "公司全称有哪些"
    answer = query_documents(query)
    print(f"问题：{query}")
    print(f"回答：{answer}") 