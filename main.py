import uvicorn
from fastapi import FastAPI
from app.api.routes import router
from app.core.logging import logger

app = FastAPI(
    title="文档问答系统 API",
    description="基于 LangChain 和 OpenAI 的文档问答系统",
    version="1.0.0",
)

app.include_router(router)

if __name__ == "__main__":
    logger.info("Starting server...")
    # 开发环境下可以设置 reload=False
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)  # 关闭自动重载
