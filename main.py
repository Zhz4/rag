import os
import argparse
from create_db import create_vector_db
from query import query_documents, query_documents_stream
import config
from api import start_server


def main():
    parser = argparse.ArgumentParser(description="文档问答系统")
    parser.add_argument("--create", action="store_true", help="强制重新创建向量数据库")
    parser.add_argument("--query", type=str, help="要查询的问题")
    parser.add_argument("--api", action="store_true", help="启动 API 服务")

    args = parser.parse_args()

    if args.api:
        print("启动 API 服务...")
        start_server()
        return

    # 检查向量数据库是否存在
    db_exists = os.path.exists(config.VECTOR_DB_PATH)

    # 如果指定了 --create 参数或向量数据库不存在，则创建向量数据库
    if args.create or not db_exists:
        print("开始创建向量数据库...")
        create_vector_db()

    # 如果提供了查询问题，执行查询
    if args.query:
        print(f"\n问题：{args.query}")
        print("回答：", end="", flush=True)
        for text_chunk in query_documents_stream(args.query):
            print(text_chunk, end="", flush=True)
        print()
    # 如果没有提供查询问题且没有指定创建数据库，进入交互模式
    elif not args.create:
        print("\n进入交互模式 (输入 'exit' 退出)")
        while True:
            question = input("\n请输入您的问题: ").strip()
            if question.lower() in ["exit", "quit", "退出"]:
                break
            if question:
                print("回答：", end="", flush=True)
                for text_chunk in query_documents_stream(question):
                    print(text_chunk, end="", flush=True)
                print()


if __name__ == "__main__":
    main()
