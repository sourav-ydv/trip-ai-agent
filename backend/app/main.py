from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command
from pydantic import BaseModel

from app.graph.build_graph import build_agent

app = FastAPI(title="Trip AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = build_agent()


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ConfirmRequest(BaseModel):
    thread_id: str
    approved: bool


def _format_result(result: dict) -> dict:
    interrupts = result.get("__interrupt__")
    if interrupts:
        return {"status": "confirmation_required", "pending_action": interrupts[0].value}
    return {"status": "ok", "response": result["messages"][-1].content}


@app.post("/chat")
def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    result = agent.invoke({"messages": [("user", req.message)]}, config=config)
    return _format_result(result)


@app.post("/confirm")
def confirm(req: ConfirmRequest):
    """Resume a graph that's paused at a booking confirmation."""
    config = {"configurable": {"thread_id": req.thread_id}}
    result = agent.invoke(Command(resume={"approved": req.approved}), config=config)
    formatted = _format_result(result)
    formatted["trace"] = [
        {"type": m.__class__.__name__, "content": str(m.content)[:300],
         "tool_calls": getattr(m, "tool_calls", None)}
        for m in result["messages"]
    ]
    return formatted


@app.get("/health")
def health():
    return {"status": "ok"}