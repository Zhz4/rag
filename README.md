# 📚 文档问答系统

一个基于向量数据库的智能文档问答系统。该系统能够处理文档，并回答与文档内容相关的问题。

## ✨ 功能特点

- 📝 文档处理和向量化存储
- 🤖 智能问答功能
- 🚀 RESTful API 接口
- 📊 可配置的日志系统
- ⚙️ 环境变量配置支持

## 🛠 技术栈

- 🐍 Python
- ⚡ FastAPI
- 🗄️ Vector Database
- 🔗 LangChain
- 🧠 OpenAI

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
OPENAI_API_KEY=
OPENAI_API_BASE= 
OPENAI_MODEL=
```

## 📖 使用方法

1. 启动服务
```bash
python main.py
```

2. API 接口

- 📤 文档上传：
  ```
  POST /upload
  ```

- ❓ 问答接口：
  ```
  POST /query/stream
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
```

## 🐳 部署方法

### Docker Compose 部署 (推荐)

1. 使用 Docker Compose 启动服务
```bash
docker compose up -d
```

2. 查看服务状态
```bash
docker compose ps
docker compose logs
```

3. 停止服务
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