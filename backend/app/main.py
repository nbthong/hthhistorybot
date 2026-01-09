from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.orchestrator.agent import agent_system
from app.models.auth import UserCreate, UserLogin, Token
from app.models.chat import ChatRequest
from app.models.auth import _get_users_collection, _hash_password, _verify_password, _create_access_token, oauth2_scheme, JWT_SECRET_KEY, JWT_ALGORITHM
from datetime import datetime
import jwt
import os
import logging
from typing import Any, Dict

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


@app.get("/")
async def root():
    return {"status": "AI Tutor is online"}


@app.post("/register")
async def register_user(payload: UserCreate):
    users = _get_users_collection()

    existing = users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email đã được đăng ký")

    hashed_pw = _hash_password(payload.password)

    user_doc: Dict[str, Any] = {
        "email": payload.email,
        "full_name": payload.full_name,
        "hashed_password": hashed_pw,
        "created_at": datetime.utcnow(),
    }

    insert_result = users.insert_one(user_doc)

    return {
        "id": str(insert_result.inserted_id),
        "email": payload.email,
        "full_name": payload.full_name,
    }


@app.post("/login", response_model=Token)
async def login_user(payload: UserLogin):
    users = _get_users_collection()

    user = users.find_one({"email": payload.email})
    if not user:
        raise HTTPException(status_code=401, detail="Email or password is incorrect")

    if not _verify_password(payload.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")

    token_data = {"sub": str(user.get("_id")), "email": user.get("email")}
    access_token = _create_access_token(token_data)

    return Token(access_token=access_token)


@app.post("/logout")
async def logout_user(token: str = Depends(oauth2_scheme)):
    try:
        jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return {"message": "Logout successfully"}

    return {"message": "Logout successfully"}

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