import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_FILE = ROOT / "knowledge" / "data.md"
PUBLIC_DIR = ROOT / "public"

SYSTEM_TEMPLATE = (
    "You are Chatbot, a helpful assistant. Answer the user's questions using ONLY "
    "the knowledge base below. If the answer is not in the knowledge base, say you "
    "don't know. Be concise.\n\n"
    "<knowledge_base>\n"
    "{knowledge}\n"
    "</knowledge_base>"
)


def load_knowledge() -> str:
    if not KNOWLEDGE_FILE.exists():
        raise RuntimeError(f"Knowledge file not found: {KNOWLEDGE_FILE}")
    return KNOWLEDGE_FILE.read_text(encoding="utf-8")


@lru_cache
def get_chain():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    llm = ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "z-ai/glm-4.5-flash"),
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.3,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_TEMPLATE),
            MessagesPlaceholder("history"),
            ("human", "{message}"),
        ],
        partial_variables={"knowledge": load_knowledge()},
    )

    return prompt | llm | StrOutputParser()


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str


app = FastAPI(title="Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        chain = get_chain()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    history = [
        HumanMessage(content=m.content) if m.role == "user" else AIMessage(content=m.content)
        for m in req.history
    ]
    reply = chain.invoke({"message": req.message, "history": history})
    return ChatResponse(reply=reply)


if PUBLIC_DIR.exists():
    app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="static")
