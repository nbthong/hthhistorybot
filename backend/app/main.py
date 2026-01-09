from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.orchestrator.agent import agent_system
from fastapi.responses import StreamingResponse
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

app = FastAPI(title="Lịch Sử 10, 11, 12 AI Tutor API")

def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if not raw:
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_user"

@app.get("/")
async def root():
    return {"status": "AI Tutor is online"}

@app.post("/chat")
async def chat(request: ChatRequest):
    user_msg = request.message
    session_id = request.session_id

    if not user_msg or not user_msg.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if len(user_msg) > 5000:
        raise HTTPException(status_code=400, detail="Message too long (max 5000 characters)",)
    
    try:
    
        intent = await agent_system.orchestrator(user_msg)

        generator_map = {
            "CHAT": agent_system.chat_agent_stream,
            "QUIZ": agent_system.quiz_agent_stream,
            "LEARN": agent_system.rag_agent_stream,
        }

        stream_fn = generator_map.get(intent, agent_system.rag_agent_stream)

        generator = stream_fn(user_msg, session_id)

        return StreamingResponse(
            generator,
            media_type="application/x-ndjson; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Content-Type-Options": "nosniff",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error("Chat endpoint error", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )