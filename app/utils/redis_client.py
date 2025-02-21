import json
import redis
from app.core.config import settings


class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )
        return cls._instance

    def save_chat_history(self, session_id: str, messages: list):
        """保存聊天历史"""
        key = f"chat:history:{session_id}"
        self.client.set(key, json.dumps(messages), ex=settings.SESSION_TTL)

    def get_chat_history(self, session_id: str) -> list:
        """获取聊天历史"""
        key = f"chat:history:{session_id}"
        history = self.client.get(key)
        return json.loads(history) if history else []
