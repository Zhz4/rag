import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# OpenAI配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
OPENAI_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 1024

# 文件路径配置
BOOKS_DIR = "./books"
FAISS_INDEX_PATH = "faiss_index"

# 文本分割配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# 向量数据库配置
VECTOR_DB_PATH = "faiss_index"
