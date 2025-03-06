FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

RUN mkdir -p logs

EXPOSE 8000

# 确保脚本具有执行权限
RUN chmod +x start.sh

CMD ["./start.sh"]
