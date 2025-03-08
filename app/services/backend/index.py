import os
from app.core.vector_store import VectorStore
from app.api.schemas.index import DeleteDocumentsRequest

from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi import UploadFile
from app.db.models.chat import files
from app.utils.minio_client import MinioClient


async def rebuild_db_serve(db):
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
        # 更新所有未学习文件的状态
        unprocessed_files = db.query(files).filter(
            files.is_study == False, files.is_deleted == False
        )
        for file in unprocessed_files:
            file.is_study = True
        db.commit()
        return {"message": "文件学习状态更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def upload_serve(files: list[UploadFile], db: Session):
    minio = MinioClient()
    try:
        results = []
        for file in files:
            content = await file.read()
            file_url = await minio.upload_file_bytes(
                file_bytes=content, object_name=file.filename
            )
            file_info = files(
                file_name=file.filename,
                file_path=file_url,
            )
            db.add(file_info)
            db.commit()
            db.refresh(file_info)
            results.append(file.filename)
        return {
            "files": results,
            "total": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


async def study_documents_serve():
    try:
        vectorstore = VectorStore.load_vectorstore()
        if not vectorstore:
            return {"message": "向量数据库不存在"}
        docstore = vectorstore.docstore
        unique_sources = {}
        documents = []
        for doc_id, doc in docstore._dict.items():
            source = doc.metadata.get("source")
            if source:
                if source not in unique_sources:
                    filename = os.path.basename(source)
                    unique_sources[source] = []
                unique_sources[source].append(doc_id)
        for source, doc_ids in unique_sources.items():
            filename = os.path.basename(source)
            documents.append(
                {
                    "ids": doc_ids,
                    "source": filename,
                    "full_path": source,
                }
            )
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def delete_documents_serve(request: DeleteDocumentsRequest):
    try:
        result = VectorStore.delete_documents(request.doc_ids)
        if result:
            return {"message": "文档向量数据已成功删除"}
        raise HTTPException(
            status_code=404, detail="删除失败，文档不存在"  # 注意这里不要包含状态码
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


async def file_list_serve(db: Session):
    try:
        files_list = (
            db.query(
                files.id,
                files.file_name,
                files.file_path,
                files.is_study,
            )
            .filter(files.is_deleted == False)
            .all()
        )
        result = [
            {
                "id": file.id,
                "file_name": file.file_name,
                "file_path": file.file_path,
                "is_study": file.is_study,
            }
            for file in files_list
        ]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件列表查询失败: {str(e)}")
