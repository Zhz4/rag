import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from app.db.models.chat import Base
from app.config.index import settings
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
            # 先删除已存在的数据库（如果需要重新创建）
            cursor.execute(f"DROP DATABASE IF EXISTS {settings.DB_NAME}")
            cursor.execute(
                f"CREATE DATABASE {settings.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
        print(f"数据库 {settings.DB_NAME} 创建成功")
    finally:
        connection.close()

    # 然后创建表
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)

    # 删除所有表（如果存在）并重新创建
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("数据表创建成功")


if __name__ == "__main__":
    init_db()
