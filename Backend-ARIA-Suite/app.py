from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agente import chat_con_agente

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[MessageItem] = []


class ChatResponse(BaseModel):
    response: str
    extracted_data: dict | None = None


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    historial = [{"role": m.role, "content": m.content} for m in req.history]
    resultado = chat_con_agente(req.message, historial)
    return ChatResponse(
        response=resultado["response"],
        extracted_data=resultado["extracted_data"],
    )
