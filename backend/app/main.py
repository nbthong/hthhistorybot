from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.orchestrator.agent import agent_system

app = FastAPI(title="Lịch Sử 12 AI Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        
        intent = agent_system.orchestrator(user_msg)
        
        if "QUIZ" in intent:
            response = agent_system.quiz_agent(user_msg)
            agent_type = "Quiz Agent"
        else:
            response = agent_system.rag_agent(user_msg)
            agent_type = "RAG Agent"
            
        return {
            "reply": response,
            "intent": intent,
            "agent": agent_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))