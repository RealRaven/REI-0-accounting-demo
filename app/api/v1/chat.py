import json
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.logging import log
from app.services.chat_service import ChatService

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    trace_id: str | None = None


@router.post("")
async def chat(req: ChatRequest):
    trace_id = req.trace_id or uuid.uuid4().hex[:12]
    log.info("chat_request", trace_id=trace_id, q=req.message[:120])
    svc = ChatService()

    async def event_stream():
        yield f"event: trace\ndata: {json.dumps({'trace_id': trace_id})}\n\n"
        async for event in svc.stream(req.message, trace_id=trace_id):
            yield f"event: {event['type']}\ndata: {json.dumps(event['data'], ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")