FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .  
COPY . .

RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

RUN mkdir -p logs books faiss_index

EXPOSE 8000

CMD ["python", "main.py"]
