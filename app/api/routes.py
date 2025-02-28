from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import asyncio
from app.api.models import Question, Answer
from app.services.document_qa import DocumentQA
from app.utils.handlers import StreamingHandler
from app.services.vector_store import VectorStore
from app.services.files import Files
from app.config.index import settings
import os
from pathlib import Path
from app.db.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
import shutil

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "文档问答系统 API 服务正在运行"}


@router.post("/rebuild-db")
async def rebuild_database():
    """重建向量数据库"""
    try:
        VectorStore.create_vectorstore()
        # 将 books 目录的文件移动到 ReadBooks 目录
        books_dir = Path("books")
        readbooks_dir = Path("ReadBooks")
        # 确保 ReadBooks 目录存在
        readbooks_dir.mkdir(exist_ok=True)
        if books_dir.exists():
            for file in books_dir.iterdir():
                if file.is_file():
                    # 使用 shutil 来复制和删除文件，而不是直接重命名
                    target_path = readbooks_dir / file.name
                    shutil.copy2(file, target_path)  # 复制文件
                    file.unlink()  # 删除原文件
        return {"message": "向量数据库重建成功，已清理文档文件"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def query_stream(question: Question, db: Session = Depends(get_db)):
    """流式问答"""
    try:
        if not os.path.exists(settings.VECTOR_DB_PATH):
            raise HTTPException(status_code=404, detail="向量数据库不存在")

        # 创建 DocumentQA 实例，传入数据库会话
        qa_system = DocumentQA(db)
        handler = StreamingHandler()
        qa_chain = await qa_system.create_qa_chain(
            session_id=question.session_id,
            streaming_handler=handler,
            user_id=question.user_id,
        )

        async def stream_response():
            task = asyncio.create_task(qa_chain.ainvoke({"question": question.text}))
            result = None

            while True:
                try:
                    token = await asyncio.wait_for(handler.queue.get(), timeout=0.1)
                    yield handler.create_sse_event(token)
                except asyncio.TimeoutError:
                    if task.done():
                        if not result:
                            result = await task
                            # 保存对话历史到Mysql
                            await qa_system.save_chat_history(
                                question.session_id,
                                question.text,
                                result["answer"],
                                question.user_id,
                            )
                            # 发送源文档信息
                            if "source_documents" in result:
                                sources = []
                                for doc in result["source_documents"]:
                                    sources.append(
                                        {
                                            "page_content": doc.page_content,
                                            "source": doc.metadata.get(
                                                "source", "未知来源"
                                            ),
                                            "page": doc.metadata.get("page", 0),
                                        }
                                    )
                                yield handler.create_sse_event(sources, is_source=True)
                        break
                    continue
                except Exception as e:
                    print(f"Error: {e}")
                    break

            yield handler.create_sse_event(None)

        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Transfer-Encoding": "chunked",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_file(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    """上传文档"""
    files_service = Files(db)
    return await files_service.uploadfile(files)

@router.get("/chat-history")
async def get_chat_history(
    session_id: str, user_id: str, db: Session = Depends(get_db)
):
    """获取聊天历史"""
    try:
        qa_system = DocumentQA(db)
        return await qa_system.get_chat_history(session_id, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-session")
async def get_session(user_id: str, db: Session = Depends(get_db)):
    """获取会话列表"""
    try:
        qa_system = DocumentQA(db)
        return await qa_system.get_session(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
