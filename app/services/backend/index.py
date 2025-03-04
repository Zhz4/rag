import os
import logging
from app.services.vector_store import VectorStore
from app.services.files import Files
from app.api.models import DeleteDocumentsRequest

from sqlalchemy.orm import Session
from fastapi import HTTPException
from pathlib import Path
from fastapi import UploadFile


async def rebuild_database(db):
    """重建向量数据库"""
    try:
        books_dir = Path("books")

        # 检查 books 目录是否存在且有文件
        if not books_dir.exists() or not any(books_dir.iterdir()):
            return {"message": "没有需要学习的文件"}

        VectorStore.create_vectorstore()
        files_service = Files(db)
        return await files_service.files_study()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def upload_file(files: list[UploadFile], db: Session):
    """上传文档"""
    files_service = Files(db)
    return await files_service.uploadfile(files)


async def study_documents():
    try:
        vectorstore = VectorStore.load_vectorstore()
        if not vectorstore:
            return {"message": "向量数据库不存在"}

        docstore = vectorstore.docstore
        # 用于追踪已处理的源文件
        unique_sources = {}  # source -> [doc_ids]
        documents = []

        for doc_id, doc in docstore._dict.items():
            source = doc.metadata.get("source")
            if source:
                if source not in unique_sources:
                    filename = os.path.basename(source)
                    unique_sources[source] = []
                unique_sources[source].append(doc_id)

        # 为每个源文件创建一个文档条目，包含其所有片段的ID
        for source, doc_ids in unique_sources.items():
            filename = os.path.basename(source)
            documents.append(
                {
                    "ids": doc_ids,  # 包含文件所有片段的ID列表
                    "source": filename,
                    "full_path": source,
                }
            )
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def delete_documents(request: DeleteDocumentsRequest):
    """删除指定文档的向量数据"""
    try:
        result = VectorStore.delete_documents(request.doc_ids)
        if result:
            return {"message": "文档向量数据已成功删除"}
        return {"message": "删除失败，可能文档不存在"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
