import asyncio
import os
from fastapi import HTTPException
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from app.db.models.chat import ChatHistory, sessions, Quote
from app.api.schemas.index import Question
from app.core.document_qa import DocumentQA
from app.utils.handlers import StreamingHandler
from app.config.index import settings


async def query_stream_serve(question: Question, db: Session):
    try:
        if not os.path.exists(settings.VECTOR_DB_PATH):
            raise HTTPException(status_code=404, detail="向量数据库不存在")
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
                            if "source_documents" in result:
                                sources = []
                                for doc in result["source_documents"]:
                                    sources.append(
                                        {
                                            "page_content": doc.page_content,
                                            "source": doc.metadata.get(
                                                "filename", "未知来源"
                                            ),
                                            "page": doc.metadata.get("page_number", 0),
                                            "html": doc.metadata.get(
                                                "text_as_html", ""
                                            ),
                                        }
                                    )
                                # TODO：保存聊天历史
                                # await qa_system.save_chat_history(
                                #     question.session_id,
                                #     question.text,
                                #     result["answer"],
                                #     question.user_id,
                                #     sources,
                                # )
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


async def chat_history_serve(session_id: str, user_id: str, db: Session):
    try:
        query = (
            db.query(ChatHistory, sessions, Quote)
            .join(sessions, ChatHistory.session_id == sessions.session_id)
            .join(
                Quote,
                ChatHistory.id == Quote.chat_history_id,
                isouter=True,
            )
        )
        if session_id:
            query = query.filter(ChatHistory.session_id == session_id)
        if user_id:
            query = query.filter(sessions.user_id == user_id)
        results = query.all()
        history = []
        current_chat = None
        for chat_history, session, quote in results:
            if current_chat is None or current_chat["id"] != chat_history.id:
                current_chat = {
                    "id": chat_history.id,
                    "question": chat_history.question,
                    "answer": chat_history.answer,
                    "session_id": chat_history.session_id,
                    "created_at": chat_history.created_at.isoformat(),
                    "quotes": [],
                }
                history.append(current_chat)
            if quote:
                current_chat["quotes"].append(
                    {
                        "content": quote.content,
                        "page_number": quote.page_number,
                        "source": quote.source,
                    }
                )
        # if not history:
        #     raise HTTPException(status_code=404, detail=f"会话 ID {session_id} 不存在")
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_session_serve(user_id: str, db: Session):
    try:
        results = (
            db.query(
                sessions.session_id.label("session_id"),
                sessions.user_id.label("user_id"),
                sessions.title.label("title"),
                sessions.created_at.label("created_at"),
            )
            .filter(sessions.user_id == user_id, sessions.is_deleted == False)
            .order_by(sessions.created_at.desc())
            .all()
        )
        return [row._asdict() for row in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
