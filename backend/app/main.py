from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.orchestrator.agent import agent_system
from fastapi.responses import StreamingResponse
import os
import logging

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

@app.get("/")
async def root():
    return {"status": "AI Tutor is online"}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        user_msg = request.message
        
        # Validate input
        if not user_msg or len(user_msg.strip()) == 0:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if len(user_msg) > 5000:
            raise HTTPException(status_code=400, detail="Message too long (max 5000 characters)")
        
        intent = await agent_system.orchestrator(user_msg)
        
        if intent == "CHAT":
            generator = agent_system.chat_agent_stream(user_msg)
        elif intent == "QUIZ":
            generator = agent_system.quiz_agent_stream(user_msg)
        else: 
            generator = agent_system.rag_agent_stream(user_msg)
            
        return StreamingResponse(
            generator,
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Content-Type-Options": "nosniff",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no", 
                "Content-Type": "application/x-ndjson; charset=utf-8",
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")