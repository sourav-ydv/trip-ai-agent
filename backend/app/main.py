import json

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _stream_events(graph_input, config: dict):
    """
    Run the agent with stream_mode="updates" so each node's output (an
    AI message deciding on a tool call, a tool's result, or an interrupt)
    is yielded as its own SSE event as soon as it happens — this is the
    live thought/action/observation trace the video's verbose=True gave
    in the terminal, now over HTTP for a frontend to render.
    """
    final_text = None
    for chunk in agent.stream(graph_input, config=config, stream_mode="updates"):
        if "__interrupt__" in chunk:
            payload = chunk["__interrupt__"][0].value
            yield _sse("interrupt", payload)
            continue

        for node_name, node_output in chunk.items():
            for m in node_output.get("messages", []):
                event_data = {
                    "node": node_name,
                    "type": m.__class__.__name__,
                    "content": m.content,
                    "tool_calls": getattr(m, "tool_calls", None),
                }
                yield _sse("step", event_data)
                if m.__class__.__name__ == "AIMessage" and m.content:
                    final_text = m.content

    yield _sse("done", {"response": final_text})


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
    return _format_result(result)


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    graph_input = {"messages": [("user", req.message)]}
    return StreamingResponse(_stream_events(graph_input, config), media_type="text/event-stream")


@app.post("/confirm/stream")
def confirm_stream(req: ConfirmRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    graph_input = Command(resume={"approved": req.approved})
    return StreamingResponse(_stream_events(graph_input, config), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok"}