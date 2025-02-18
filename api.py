from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import os
from create_db import create_vector_db
from query import query_documents, query_documents_stream_for_api
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


@app.post("/query/stream")
async def query_stream(question: Question):
    try:
        if not os.path.exists(config.VECTOR_DB_PATH):
            create_vector_db()

        return StreamingResponse(
            query_documents_stream_for_api(question.text),
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
