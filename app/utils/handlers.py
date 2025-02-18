from langchain.callbacks.base import BaseCallbackHandler
import asyncio
import json

class StreamingHandler(BaseCallbackHandler):
    """处理流式输出的回调处理器"""

    def __init__(self):
        self.queue = asyncio.Queue()

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """处理流式输出的每个token"""
        await self.queue.put(token)

    def create_sse_event(self, token):
        """创建 SSE 事件"""
        return f"data: {json.dumps({'choices': [{'delta': {'content': token}}]}, ensure_ascii=False)}\n\n" 