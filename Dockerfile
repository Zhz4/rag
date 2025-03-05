FROM python:3.10-slim

WORKDIR /app

COPY . .

# 在安装 Python 包之前，先安装必要的构建工具
RUN apt-get update && apt-get install -y \
    build-essential \
    make \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

RUN mkdir -p logs books faiss_index ReadBooks

EXPOSE 8000

# 确保脚本具有执行权限
RUN chmod +x start.sh

CMD ["./start.sh"]
