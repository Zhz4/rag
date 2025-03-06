# 📚 RAG文档问答系统

一个基于Langchain的RAG文档检索增强生成系统。该系统能够处理文档，并回答与文档内容相关的问题。

## ✨ 功能特点

- 📝 文档处理和向量化存储
- 🤖 智能问答功能
- 🚀 RESTful API 接口
- 📊 可配置的日志系统
- ⚙️ 环境变量配置支持

## 🛠 技术栈

- 🐍 Python
- 🔗 LangChain
- ⚡ FastAPI
- 🗄️ Vector Database
- 📦 MinIO
- �� Docker
- 🎲 MySQL

## 🚀 安装说明

1. 克隆项目
```bash
git clone [项目地址]
cd [项目名称]
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
复制 `.env.example` 到 `.env` 并填写必要的配置：
```
OPENAI_API_KEY=  // 大模型的key
OPENAI_API_BASE=  // 大模型代理地址
OPENAI_MODEL=  // 大模型名称

# MinIO配置
MINIO_ENDPOINT=localhost:9000  // MinIO服务地址
MINIO_ACCESS_KEY=minioadmin   // MinIO访问密钥
MINIO_SECRET_KEY=minioadmin   // MinIO密钥
MINIO_BUCKET_NAME=docqa      // MinIO存储桶名称
MINIO_SECURE=False          // 是否启用HTTPS
```

## 📖 使用方法
1. 初始化mysql数据库
```bash
python scripts/init_db.py
```

2. 启动服务
```bash
python main.py
```

3. API 接口

- 📤 文档上传：
  ```
  POST /upload
  ```

- ❓ 问答接口：
  ```
  POST /query/stream
  ```
- 🚿 重构向量数据库：
  ```
  POST /rebuild-db
  ```
## 📁 项目结构

```
app/
├── api/
│   └── routes.py
├── core/
│   ├── config.py
│   └── logging.py
├── services/
│   ├── document_qa.py
│   └── vector_store.py
├── utils/
│   ├── minio_client.py    # MinIO客户端工具
│   └── handlers.py
```

## 🐳 部署方法

### Docker Compose 部署 (推荐)

1. 使用 Docker Compose 构建镜像
```bash
docker compose build
```

2. 使用 Docker Compose 启动服务
```bash
docker compose up -d
```

3. 查看服务状态
```bash
docker compose ps
docker compose logs
```

4. 停止服务
```bash
docker compose down
```

### Docker 部署

1. 构建 Docker 镜像
```bash
docker build -t doc-qa-system .
```

2. 运行容器
```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name doc-qa-system \
  doc-qa-system
```

3. 查看容器运行状态
```bash
docker ps
docker logs doc-qa-system
```

4. 停止和删除容器
```bash
docker stop doc-qa-system
docker rm doc-qa-system
```

### MinIO 服务访问

部署完成后，可以通过以下地址访问MinIO服务：

- MinIO API: http://localhost:9000
- MinIO Console: http://localhost:9001

默认登录凭证：
- 用户名：admin
- 密码：admin123

```mermaid
graph TD
    A[用户] --> B[FastAPI 服务]
    
    subgraph 文档处理流程
        C[文档上传 POST /upload] --> D[MinIO存储]
        D --> E[向量化处理]
        E --> F[FAISS向量数据库]
    end
    
    subgraph 问答流程
        G[问题查询 POST /query/stream] --> H[LangChain检索]
        H --> I[向量相似度搜索]
        I --> J[OpenAI模型生成答案]
        J --> K[流式返回答案]
    end
    
    subgraph 数据存储
        L[(MySQL数据库)]
        M[(MinIO对象存储)]
        N[(FAISS向量库)]
    end
    
    B --> C
    B --> G
    F --> I
    D --> M
    
    %% 数据流向
    L --> |存储会话记录|B
    M --> |存储原始文档|B
    N --> |存储文档向量|B