from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


@app.post("/chat")
def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    result = agent.invoke({"messages": [("user", req.message)]}, config=config)
    return {
        "response": result["messages"][-1].content,
        "trace": [
            {"type": m.__class__.__name__, "content": str(m.content)[:300],
             "tool_calls": getattr(m, "tool_calls", None)}
            for m in result["messages"]
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok"}
