from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.orchestrator.agent import agent_system
from fastapi.responses import StreamingResponse
import os

app = FastAPI(title="Lịch Sử 12 AI Tutor API")

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
        intent = await agent_system.orchestrator(user_msg)
        if "QUIZ" in intent:
            generator = agent_system.quiz_agent_stream(user_msg)
        else:
            generator = agent_system.rag_agent_stream(user_msg)
            
        return StreamingResponse(
            generator,
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "X-Content-Type-Options": "nosniff",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))