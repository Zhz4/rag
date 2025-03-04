from fastapi import HTTPException
import asyncio
from app.api.models import Question
from app.services.document_qa import DocumentQA
from app.utils.handlers import StreamingHandler
from app.config.index import settings
import os
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import StreamingResponse


async def query_stream(question: Question, db: Session):
    """流式问答"""
    try:
        if not os.path.exists(settings.VECTOR_DB_PATH):
            raise HTTPException(status_code=404, detail="向量数据库不存在")

        # 创建 DocumentQA 实例，传入数据库会话
        qa_system = DocumentQA(db)
        handler = StreamingHandler()
        qa_chain = await qa_system.create_qa_chain(
            session_id=question.session_id,
            streaming_handler=handler,
            user_id=question.user_id,
        )

        async def stream_response():
            task = asyncio.create_task(qa_chain.ainvoke({"question": question.text}))
            result = None

            while True:
                try:
                    token = await asyncio.wait_for(handler.queue.get(), timeout=0.1)
                    yield handler.create_sse_event(token)
                except asyncio.TimeoutError:
                    if task.done():
                        if not result:
                            result = await task
                            # 保存对话历史到Mysql
                            await qa_system.save_chat_history(
                                question.session_id,
                                question.text,
                                result["answer"],
                                question.user_id,
                            )
                            # 发送源文档信息
                            if "source_documents" in result:
                                sources = []
                                for doc in result["source_documents"]:
                                    sources.append(
                                        {
                                            "page_content": doc.page_content,
                                            "source": doc.metadata.get(
                                                "source", "未知来源"
                                            ),
                                            "page": doc.metadata.get("page", 0),
                                        }
                                    )
                                yield handler.create_sse_event(sources, is_source=True)
                        break
                    continue
                except Exception as e:
                    print(f"Error: {e}")
                    break

            yield handler.create_sse_event(None)

        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Transfer-Encoding": "chunked",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_chat_history(session_id: str, user_id: str, db: Session):
    """获取聊天历史"""
    try:
        qa_system = DocumentQA(db)
        return await qa_system.get_chat_history(session_id, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_session(user_id: str, db: Session):
    """获取会话列表"""
    try:
        qa_system = DocumentQA(db)
        return await qa_system.get_session(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))