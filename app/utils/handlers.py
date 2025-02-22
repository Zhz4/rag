from langchain.callbacks.base import BaseCallbackHandler
import asyncio
import json


class StreamingHandler(BaseCallbackHandler):
    """处理流式输出的回调处理器"""

    def __init__(self):
        self.queue = asyncio.Queue()
        self.source_documents = None
        self.is_answer_phase = False  # 添加标志来跟踪是否在答案阶段

    async def on_llm_start(self, *args, **kwargs) -> None:
        """当 LLM 开始生成时被调用"""
        self.is_answer_phase = True

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """处理流式输出的每个token"""
        if self.is_answer_phase:  # 只有在答案阶段才输出token
            await self.queue.put(token)

    def create_sse_event(self, token, is_source=False):
        """创建 SSE 事件"""
        # 如果是 None 则直接返回 DONE 标记
        if token is None:
            return "data: [DONE]\n\n"

        if is_source and token:
            return f"data: {json.dumps({'sources': token}, ensure_ascii=False)}\n\n"
        return f"data: {json.dumps({'choices': [{'delta': {'content': token}}]}, ensure_ascii=False)}\n\n"
