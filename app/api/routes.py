from fastapi import APIRouter, UploadFile, File, Query, Depends, Body, HTTPException
from sqlalchemy.orm import Session
from app.api.schemas.index import (
    Question,
    DeleteDocumentsRequest,
)
from app.db.database import get_db
from app.services.backend.index import (
    rebuild_db_serve,
    upload_serve,
    study_documents_serve,
    delete_documents_serve,
    file_list_serve,
)
from app.services.frontend.index import (
    query_stream_serve,
    chat_history_serve,
    get_session_serve,
)
from app.api.response import success_response, error_response

router = APIRouter()


@router.post("/rebuild-db", summary="重建数据库", tags=["后台管理"])
async def rebuild_db(db: Session = Depends(get_db)):
    try:
        result = await rebuild_db_serve(db)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e))


@router.post("/upload", summary="上传文件", tags=["后台管理"])
async def upload(
    files: list[UploadFile] = File(..., description="文档文件列表"),
    db: Session = Depends(get_db),
):
    try:
        result = await upload_serve(files, db)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e))


@router.get("/study-documents", summary="模型已学习的所有片段", tags=["后台管理"])
async def study_documents():
    try:
        result = await study_documents_serve()
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e))


@router.get("/file-list", summary="文件列表", tags=["后台管理"])
async def file_list(db: Session = Depends(get_db)):
    try:
        result = await file_list_serve(db)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=e)


@router.post("/delete-documents", summary="模型删除文档", tags=["后台管理"])
async def delete_documents(
    request: DeleteDocumentsRequest = Body(..., description="要删除的文档信息")
):
    try:
        result = await delete_documents_serve(request)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e))


@router.post("/query/stream", summary="模型问答", tags=["前台页面"])
async def query_stream(
    question: Question = Body(..., description="用户提问内容"),
    db: Session = Depends(get_db),
):
    return await query_stream_serve(question, db)


@router.get("/chat-history", summary="获取聊天记录", tags=["前台页面"])
async def chat_history(
    session_id: str = Query(..., description="会话ID"),
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db),
):
    try:
        result = await chat_history_serve(session_id, user_id, db)
        if not result:
            raise HTTPException(status_code=404, detail=f"会话 ID {session_id} 不存在")
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e))


@router.get("/get-session", summary="获取会话", tags=["前台页面"])
async def get_session(
    user_id: str = Query(..., description="用户ID"), db: Session = Depends(get_db)
):
    try:
        result = await get_session_serve(user_id, db)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e))
