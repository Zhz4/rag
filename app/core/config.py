from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    # OpenAI配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    MAX_TOKENS: int = 1024

    # 文件路径配置
    BOOKS_DIR: str = "./books"
    FAISS_INDEX_PATH: str = "faiss_index"
    VECTOR_DB_PATH: str = "faiss_index"

    # 文本分割配置
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50


settings = Settings()
