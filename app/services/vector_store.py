from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyMuPDFLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config.index import settings
from app.logging.logging import logger
import os
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.chat import files


class VectorStore:
    @staticmethod
    def load_documents():
        """加载文档"""
        documents = []

        # 加载 PDF 文件
        pdf_files = [f for f in os.listdir(settings.BOOKS_DIR) if f.endswith(".pdf")]
        for pdf_file in pdf_files:
            pdf_path = os.path.join(settings.BOOKS_DIR, pdf_file)
            logger.info(f"正在加载文件：{pdf_path}")
            loader = PyMuPDFLoader(pdf_path)
            documents.extend(loader.load())

        # 加载 CSV 文件
        csv_files = [f for f in os.listdir(settings.BOOKS_DIR) if f.endswith(".csv")]
        for csv_file in csv_files:
            csv_path = os.path.join(settings.BOOKS_DIR, csv_file)
            logger.info(f"正在加载文件：{csv_path}")
            loader = CSVLoader(csv_path)
            documents.extend(loader.load())

        return documents

    @staticmethod
    def create_vectorstore():
        """创建或更新向量数据库"""
        # 检查是否已存在向量数据库
        if (
            os.path.exists(settings.FAISS_INDEX_PATH)
            and os.path.isdir(settings.FAISS_INDEX_PATH)
            and len(os.listdir(settings.FAISS_INDEX_PATH)) > 0
        ):
            logger.info("检测到已存在的向量数据库，执行增量更新")
            existing_vectorstore = VectorStore.load_vectorstore()
            documents = VectorStore.load_documents()

            # 创建新文档的向量嵌入
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP
            )
            new_docs = text_splitter.split_documents(documents)

            # 将新文档添加到现有向量库
            existing_vectorstore.add_documents(new_docs)
            existing_vectorstore.save_local(settings.FAISS_INDEX_PATH)
            logger.info("向量索引已更新")
            return existing_vectorstore

        # 如果不存在，创建新的向量数据库
        documents = VectorStore.load_documents()
        logger.info(f"共加载 {len(documents)} 个文档片段")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP
        )
        docs = text_splitter.split_documents(documents)
        logger.info(f"文本切分完成，共生成 {len(docs)} 个文本块")

        embedding = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_API_BASE,
        )

        vectorstore = FAISS.from_documents(docs, embedding)
        vectorstore.save_local(settings.FAISS_INDEX_PATH)
        logger.info("向量索引已保存")
        return vectorstore

    @staticmethod
    def load_vectorstore():
        """加载向量数据库"""
        embedding = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_API_BASE,
        )
        return FAISS.load_local(
            settings.FAISS_INDEX_PATH, embedding, allow_dangerous_deserialization=True
        )

    @staticmethod
    def delete_documents(file_paths: list[str]):
        """删除指定文档的向量数据
        Args:
            file_paths: 要删除的文档路径列表
        """
        try:
            vectorstore = VectorStore.load_vectorstore()
            if not vectorstore:
                logger.warning("向量数据库不存在")
                return False

            # 获取所有文档的元数据
            docstore = vectorstore.docstore

            # 找到要删除的文档的 IDs
            docs_to_delete = []
            for doc_id, doc in docstore._dict.items():
                doc_source = doc.metadata.get("source")
                for file_path in file_paths:
                    full_path = os.path.join(settings.BOOKS_DIR, file_path)
                    if doc_source == full_path:
                        docs_to_delete.append(doc_id)
                        break

            if not docs_to_delete:
                logger.warning("未找到指定文档的向量数据")
                return False

            # 删除文档
            vectorstore.delete(docs_to_delete)

            # 保存更新后的向量数据库
            vectorstore.save_local(settings.FAISS_INDEX_PATH)
            logger.info(f"成功删除 {len(docs_to_delete)} 个文档的向量数据")

            # 变更数据库状态为未学习
            db = next(get_db())
            for file_path in file_paths:
                file = (
                    db.query(files).filter(files.file_local_path == file_path).first()
                )
                if file:
                    file.is_study = False
                    db.commit()
                    db.refresh(file)

            # 将文件从ReadBooks目录中删除
            for file_path in file_paths:
                os.remove(os.path.join(settings.READ_BOOKS_DIR, file_path))

            return True

        except Exception as e:
            logger.error(f"删除向量数据时发生错误: {str(e)}")
            return False
