from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import asyncio
from app.api.models import Question, Answer
from app.services.document_qa import DocumentQA
from app.utils.handlers import StreamingHandler
from app.services.vector_store import VectorStore
from app.core.config import settings
import os
from pathlib import Path

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "文档问答系统 API 服务正在运行"}


@router.post("/rebuild-db")
async def rebuild_database():
    try:
        VectorStore.create_vectorstore()
        return {"message": "向量数据库重建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def query_stream(question: Question):
    try:
        if not os.path.exists(settings.VECTOR_DB_PATH):
            VectorStore.create_vectorstore()

        handler = StreamingHandler()
        qa_system = DocumentQA()
        qa_chain = qa_system.create_qa_chain(streaming_handler=handler)

        async def stream_response():
            task = asyncio.create_task(qa_chain.ainvoke({"question": question.text}))

            while True:
                try:
                    token = await asyncio.wait_for(handler.queue.get(), timeout=0.1)
                    yield handler.create_sse_event(token)
                except asyncio.TimeoutError:
                    if task.done():
                        break
                    continue
                except Exception as e:
                    print(f"Error: {e}")
                    break

            yield handler.create_sse_event(None)
            yield "data: [DONE]\n\n"

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
async def upload_file(file: UploadFile = File(...)):
    try:
        # 确保 books 目录存在
        books_dir = Path("books")
        books_dir.mkdir(exist_ok=True)

        # 构建文件保存路径
        file_path = books_dir / file.filename

        # 写入文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # 重建向量数据库
        # VectorStore.create_vectorstore()

        return {"message": "文件上传成功", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
