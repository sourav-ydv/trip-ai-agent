# Trip AI Agent

A LangGraph agent that plans a trip end to end — flights/trains, hotels,
attractions, local transport, weather — by reasoning over tools and asking
for your preferences instead of guessing. Built this to actually understand
how agent orchestration works beyond toy examples, not just call an LLM once
and call it a day.

Everything here runs on free tiers, no card needed anywhere.

## How it's put together

- **LLM**: Groq (`openai/gpt-oss-120b`) — fast and free, handles tool calling well
- **Flights & hotels**: SerpApi's Google Flights / Google Hotels engines
- **Weather**: OpenWeatherMap
- **Attractions & trains**: plain DuckDuckGo search, since there's no free
  public train-fare API — the agent is told to flag these numbers as
  unconfirmed rather than present them as fact
- **Cabs**: a simulated fare estimate, clearly labeled as such (again, no
  free public cab-booking API exists)
- **Orchestration**: LangGraph's `create_react_agent` with a `SqliteSaver`
  checkpointer, so a conversation thread remembers what's already been said
- **Booking safety**: `book_flight`/`book_hotel` are separate simulated-booking
  tools that call LangGraph's `interrupt()`, pausing the whole run and
  requiring an explicit approve/deny before completing — one pause per
  booking action, so a round-trip needs two separate confirmations
- **Streaming**: `/chat/stream` and `/confirm/stream` yield Server-Sent Events
  as the agent works — each tool call, each tool result, and each pause for
  confirmation — instead of waiting for the whole run to finish

## Running it

```
cd backend
python -m venv venv
source venv/bin/activate      # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:
- `GROQ_API_KEY` — console.groq.com
- `SERPAPI_API_KEY` — serpapi.com (free plan)
- `OPENWEATHER_API_KEY` — openweathermap.org

Then:
```
uvicorn app.main:app --reload --port 8000
```

### Non-streaming (simplest, good for quick tests)

```
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a budget trip from Delhi to Goa, 1 to 7 May 2027", "thread_id": "test1"}'
```

Keep using the same `thread_id` to continue a planning session.

If the agent decides to book something, this responds with
`{"status": "confirmation_required", "pending_action": {...}}` instead of a
normal answer. Approve or deny it with:
```
curl -X POST http://localhost:8000/confirm \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "test1", "approved": true}'
```

### Streaming (what a real frontend will use)

Same request/response shape, but hits `/chat/stream` and `/confirm/stream`
instead, and streams Server-Sent Events as the agent works rather than
blocking until it's done. Each event is one of:

- `event: step` — an AI message deciding on a tool call, or a tool's result
- `event: interrupt` — the agent paused, waiting for a booking confirmation
- `event: done` — the run finished (or paused); `data.response` has the
  final text, or `null` if it stopped at an interrupt instead

On Windows, PowerShell mangles inline JSON with curl, so write the payload
to a file first (put scratch test payloads under `backend/scratch/` —
that folder is gitignored):

```
'{"message": "...", "thread_id": "t1"}' | Out-File -Encoding utf8 scratch/body.json
curl.exe -N -X POST http://localhost:8000/chat/stream -H "Content-Type: application/json" -d "@scratch/body.json"
```

(`-N` disables curl's output buffering so events print as they arrive
instead of all at once at the end.)

## Where this stands right now

Working: multi-step reasoning over tools, live flight/hotel/weather data,
conversation memory that survives a restart (SQLite-backed checkpointer), a
prompt rule that stops the model from inventing exact train numbers or hotel
names when a search comes back empty, a human-confirmation gate before any
simulated booking completes, and SSE streaming of the whole reasoning trace.

Not done yet: no frontend — this is backend/API only for now. Also worth
noting: the agent sometimes asks "should I book this?" in plain text even
after being told to just book it, instead of calling the tool directly (the
system prompt could be tightened here, but the actual safety gate — the
`interrupt()` call inside the booking tools — works correctly regardless).