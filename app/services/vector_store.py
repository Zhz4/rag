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
    def delete_documents(doc_ids: list[str]):
        """删除指定文档的向量数据
        Args:
            doc_ids: 要删除的文档ID列表
        """
        try:
            vectorstore = VectorStore.load_vectorstore()
            if not vectorstore:
                logger.warning("向量数据库不存在")
                return False

            docstore = vectorstore.docstore

            # 打印删除前的文档数量
            logger.info(f"删除前文档总数: {len(docstore._dict)}")
            logger.info(f"要删除的文档IDs: {doc_ids}")

            # 验证所有文档ID是否存在
            docs_to_delete = []
            file_paths_to_update = set()
            for doc_id in doc_ids:
                logger.info(f"检查文档ID: {doc_id}")
                if doc_id in docstore._dict:
                    docs_to_delete.append(doc_id)
                    source = docstore._dict[doc_id].metadata.get("source")
                    logger.info(f"找到文档，源文件: {source}")
                    if source:
                        relative_path = os.path.relpath(source, settings.BOOKS_DIR)
                        file_paths_to_update.add(relative_path)
                else:
                    logger.warning(f"文档ID不存在: {doc_id}")

            if not docs_to_delete:
                logger.warning("未找到指定文档的向量数据")
                return False

            # 删除文档
            logger.info(f"开始删除文档: {docs_to_delete}")
            vectorstore.delete(docs_to_delete)

            # 验证删除结果
            logger.info(f"删除后文档总数: {len(docstore._dict)}")
            for doc_id in docs_to_delete:
                if doc_id in docstore._dict:
                    logger.error(f"文档 {doc_id} 删除失败")
                else:
                    logger.info(f"文档 {doc_id} 删除成功")

            # 保存更新后的向量数据库
            vectorstore.save_local(settings.FAISS_INDEX_PATH)
            logger.info(f"成功删除 {len(docs_to_delete)} 个文档的向量数据")

            # 变更数据库状态为未学习
            db = next(get_db())
            for file_path in file_paths_to_update:
                file = (
                    db.query(files).filter(files.file_local_path == file_path).first()
                )
                if file:
                    file.is_study = False
                    db.commit()
                    db.refresh(file)

                # 将文件从ReadBooks目录中删除
                read_books_path = os.path.join(settings.READ_BOOKS_DIR, file_path)
                if os.path.exists(read_books_path):
                    os.remove(read_books_path)

            return True

        except Exception as e:
            logger.error(f"删除向量数据时发生错误: {str(e)}")
            return False
