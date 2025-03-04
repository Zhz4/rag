from fastapi import APIRouter, UploadFile, File
from app.api.models import Question,DeleteDocumentsRequest
from app.db.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from app.services.backend.index import rebuild_database,upload_file,study_documents,delete_documents
from app.services.chat.index import query_stream,get_chat_history,get_session
router = APIRouter()


"""
后台管理
"""
@router.post("/rebuild-db")
async def rebuild_db(db:Session = Depends(get_db)):
    return await rebuild_database(db)

@router.post("/upload")
async def upload_file_handler(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    return await upload_file(files, db)


@router.get("/study-documents")
async def study_documents_handler():
    return await study_documents()

@router.post("/delete-documents")
async def delete_documents_handler(request: DeleteDocumentsRequest):
    return await delete_documents(request)


"""
前台
"""
@router.post("/query/stream")
async def query_stream_handler(question: Question, db: Session = Depends(get_db)):
    return await query_stream(question, db)


@router.get("/chat-history")
async def get_chat_history_handler(session_id: str, user_id: str, db: Session = Depends(get_db)):
    return await get_chat_history(session_id, user_id, db)


@router.get("/get-session")
async def get_session_handler(user_id: str, db: Session = Depends(get_db)):
    return await get_session(user_id, db)

