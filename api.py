from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import os
from create_db import create_vector_db
from query import query_documents, query_documents_stream
import config
import json
from typing import AsyncGenerator

app = FastAPI(
    title="文档问答系统 API",
    description="基于 LangChain 和 OpenAI 的文档问答系统",
    version="1.0.0",
)


class Question(BaseModel):
    text: str


class Answer(BaseModel):
    question: str
    answer: str


@app.get("/")
async def root():
    return {"message": "文档问答系统 API 服务正在运行"}


@app.post("/rebuild-db")
async def rebuild_database():
    try:
        create_vector_db()
        return {"message": "向量数据库重建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def query(question: Question):
    try:
        # 检查向量数据库是否存在
        if not os.path.exists(config.VECTOR_DB_PATH):
            create_vector_db()

        answer = query_documents(question.text)
        return Answer(question=question.text, answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def stream_generator(question: str) -> AsyncGenerator[str, None]:
    """异步生成器，用于流式传输响应"""
    try:
        for chunk in query_documents_stream(question):
            # 使用 SSE 格式
            yield f"data: {json.dumps({'content': chunk, 'done': False}, ensure_ascii=False)}\n\n"
        # 发送完成标记
        yield f"data: {json.dumps({'content': '', 'done': True}, ensure_ascii=False)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"


@app.post("/query/stream")
async def query_stream(question: Question):
    try:
        if not os.path.exists(config.VECTOR_DB_PATH):
            create_vector_db()

        return StreamingResponse(
            stream_generator(question.text),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Transfer-Encoding": "chunked",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def start_server():
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start_server()
