import os
import logging
from app.services.vector_store import VectorStore
from app.services.files import Files
from app.api.models import DeleteDocumentsRequest

from sqlalchemy.orm import Session
from fastapi import HTTPException
from pathlib import Path
from fastapi import UploadFile
from app.db.models.chat import files


async def rebuild_database(db):
    """重建向量数据库"""
    try:
        # 检查是否有未学习的文件
        unprocessed_files = (
            db.query(files)
            .filter(files.is_study == False, files.is_deleted == False)
            .count()
        )

        if unprocessed_files == 0:
            return {"message": "没有需要学习的文件"}

        await VectorStore.create_vectorstore(db)
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
        # 如果文档不存在，直接抛出 HTTPException
        raise HTTPException(
            status_code=404, detail="删除失败，文档不存在"  # 注意这里不要包含状态码
        )
    except Exception as e:
        # 如果是 HTTPException 就直接往上抛
        if isinstance(e, HTTPException):
            raise e
        # 其他异常包装成 500
        raise HTTPException(status_code=500, detail=str(e))


async def file_list(db: Session):
    try:
        files_service = Files(db)
        return await files_service.files_list()
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        # 其他异常包装成 500
        raise HTTPException(status_code=500, detail=str(e))
