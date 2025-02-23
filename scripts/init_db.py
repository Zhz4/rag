import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from app.db.models.chat import Base
from app.core.config import settings
from sqlalchemy import create_engine, text
import pymysql


def init_db():
    # 首先创建数据库
    connection = pymysql.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}")
        connection.commit()
        print(f"数据库 {settings.DB_NAME} 创建成功")
    finally:
        connection.close()

    # 然后创建表
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("数据表创建成功")


if __name__ == "__main__":
    init_db()
