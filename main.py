import uvicorn
from fastapi import FastAPI
from app.api.routes import router
from app.core.logging import logger
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="文档问答系统 API",
    description="基于 LangChain 和 OpenAI 的文档问答系统",
    version="1.0.0",
)
# 配置 CORS
origins = [
    "http://localhost:3000",     # React 默认端口
    "http://localhost:8080",     # Vue 默认端口
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "http://localhost:5173",     # Vite 默认端口
    "http://127.0.0.1:5173",
    "*"                          # 允许所有源（生产环境建议设置具体的域名）
]

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],         # 允许所有 HTTP 方法
    allow_headers=["*"],         # 允许所有 headers
    expose_headers=["*"],        # 允许暴露所有 headers
    max_age=3600,               # 预检请求的缓存时间（秒）
)
app.include_router(router)

if __name__ == "__main__":
    logger.info("Starting server...")
    # 开发环境下可以设置 reload=False
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)  # 关闭自动重载
