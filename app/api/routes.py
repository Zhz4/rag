from fastapi import APIRouter, UploadFile, File, Query, Depends, Body
from sqlalchemy.orm import Session

from app.api.models import (
    Question,
    DeleteDocumentsRequest,
)
from app.db.database import get_db
from app.services.backend.index import (
    rebuild_database,
    upload_file,
    study_documents,
    delete_documents,
)
from app.services.chat.index import query_stream, get_chat_history, get_session
from app.api.response import success_response, error_response

router = APIRouter()


"""
后台管理
"""


@router.post("/rebuild-db", summary="重建数据库", tags=["后台管理"])
async def rebuild_db(db: Session = Depends(get_db)):
    try:
        result = await rebuild_database(db)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e))


@router.post("/upload", summary="上传文件", tags=["后台管理"])
async def upload_file_handler(
    files: list[UploadFile] = File(..., description="文档文件列表"),
    db: Session = Depends(get_db),
):
    try:
        result = await upload_file(files, db)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e))


@router.get("/study-documents", summary="模型学习文档", tags=["后台管理"])
async def study_documents_handler():
    try:
        result = await study_documents()
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e))


@router.post("/delete-documents", summary="模型删除文档", tags=["后台管理"])
async def delete_documents_handler(
    request: DeleteDocumentsRequest = Body(..., description="要删除的文档信息")
):
    try:
        result = await delete_documents(request)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e))


"""
前台
"""


@router.post("/query/stream", summary="模型问答", tags=["前台页面"])
async def query_stream_handler(
    question: Question = Body(..., description="用户提问内容"),
    db: Session = Depends(get_db),
):
    return await query_stream(question, db)


@router.get("/chat-history", summary="获取聊天记录", tags=["前台页面"])
async def get_chat_history_handler(
    session_id: str = Query(..., description="会话ID"),
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db),
):
    try:
        result = await get_chat_history(session_id, user_id, db)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e))


@router.get("/get-session", summary="获取会话", tags=["前台页面"])
async def get_session_handler(
    user_id: str = Query(..., description="用户ID"), db: Session = Depends(get_db)
):
    try:
        result = await get_session(user_id, db)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e))
