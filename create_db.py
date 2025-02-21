import os
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyMuPDFLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import config


def load_documents():
    documents = []

    # 加载 PDF 文件
    pdf_files = [f for f in os.listdir(config.BOOKS_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print("⚠️ 没有找到 PDF 文件，请检查 books 文件夹！")
    else:
        print(f"📂 在 books 文件夹中找到 {len(pdf_files)} 个 PDF 文件，开始加载...")

    for pdf_file in pdf_files:
        pdf_path = os.path.join(config.BOOKS_DIR, pdf_file)
        print(f"📖 正在加载文件：{pdf_path}")
        loader = PyMuPDFLoader(pdf_path)
        documents.extend(loader.load())

    # 加载 CSV 文件
    csv_files = [f for f in os.listdir(config.BOOKS_DIR) if f.endswith(".csv")]
    if not csv_files:
        print("⚠️ 没有找到 CSV 文件，请检查 books 文件夹！")
    else:
        print(f"📂 在 books 文件夹中找到 {len(csv_files)} 个 CSV 文件，开始加载...")

    for csv_file in csv_files:
        csv_path = os.path.join(config.BOOKS_DIR, csv_file)
        print(f"📖 正在加载文件：{csv_path}")
        loader = CSVLoader(csv_path)
        documents.extend(loader.load())

    return documents


def create_vector_db():
    # 1. 加载文档
    documents = load_documents()
    print(f"✅ 共加载 {len(documents)} 个文档片段，开始进行文本切分...")

    # 2. 文本切分
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP
    )
    docs = text_splitter.split_documents(documents)
    print(f"📄 文本切分完成，共生成 {len(docs)} 个文本块。")

    # 3. 初始化 Embeddings
    embedding = OpenAIEmbeddings(
        openai_api_key=config.OPENAI_API_KEY,
        openai_api_base=config.OPENAI_API_BASE,
    )

    # 4. 创建向量存储
    print("📡 构建 FAISS 向量存储...")
    vectorstore = FAISS.from_documents(docs, embedding)

    # 5. 保存索引
    vectorstore.save_local(config.FAISS_INDEX_PATH)
    print("✅ 向量索引已保存！")


if __name__ == "__main__":
    create_vector_db()
