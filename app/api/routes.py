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
        # 将 books 目录的文件移动到 ReadBooks 目录
        books_dir = Path("books")
        readbooks_dir = Path("ReadBooks")
        # 确保 ReadBooks 目录存在
        readbooks_dir.mkdir(exist_ok=True)
        if books_dir.exists():
            for file in books_dir.iterdir():
                if file.is_file():
                    # 移动文件到 ReadBooks 目录
                    file.rename(readbooks_dir / file.name)
        return {"message": "向量数据库重建成功，已清理文档文件"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def query_stream(question: Question):
    try:
        if not os.path.exists(settings.VECTOR_DB_PATH):
            raise HTTPException(status_code=404, detail="向量数据库不存在")

        # 创建 DocumentQA 实例
        qa_system = DocumentQA()
        handler = StreamingHandler()
        qa_chain = qa_system.create_qa_chain(
            session_id=question.session_id, streaming_handler=handler
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
                            # 保存对话历史到Redis
                            qa_system.save_chat_history(
                                question.session_id, question.text, result["answer"]
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
async def upload_file(files: list[UploadFile] = File(...)):
    try:
        # 确保 books 目录存在
        books_dir = Path("books")
        books_dir.mkdir(exist_ok=True)

        uploaded_files = []
        for file in files:
            # 构建文件保存路径
            file_path = books_dir / file.filename

            # 写入文件
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            uploaded_files.append(file.filename)

        return {
            "message": "文件上传成功",
            "uploaded_files": uploaded_files,
            "total_files": len(uploaded_files),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
