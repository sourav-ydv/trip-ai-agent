# Trip AI Agent

A LangGraph agent that plans a trip end to end — flights/trains, hotels,
attractions, local transport, weather — by reasoning over tools and asking
for your preferences instead of guessing. Built this to actually understand
how agent orchestration works beyond toy examples, not just call an LLM once
and call it a day.

Everything here runs on free tiers, no card needed anywhere.

## How it's put together

**Backend**
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
- **Booking safety**: `book_flight`/`book_hotel` are simulated-booking tools
  (no real payment or reservation is ever made anywhere) that call
  LangGraph's `interrupt()`, pausing the run and requiring an explicit
  approve/deny before completing — one pause per booking action, so a
  round-trip needs two separate confirmations
- **Streaming**: `/chat/stream` and `/confirm/stream` yield Server-Sent
  Events as the agent works — each tool call, each result, each pause for
  confirmation — instead of waiting for the whole run to finish
- **Context management**: conversation history is trimmed to a token budget
  before every LLM call (a rough char-based estimate, not a real tokenizer)
  to stay under Groq's free-tier per-minute limit; a system-prompt rule
  also tells the model not to re-dump the full itinerary/cost table on
  every turn, since that was the main source of token bloat
- **Rate-limit handling**: a Groq `RateLimitError` (per-minute or per-day
  free-tier cap) comes back as a clean `{"status": "error", ...}` response
  instead of crashing the request

**Frontend**
- React + Vite chat UI
- Renders a dedicated confirmation card with Approve/Decline buttons when
  the backend pauses on a booking, instead of expecting the user to type a
  reply — matches the backend's requirement that a paused thread can only be
  resumed via `/confirm`, not a new chat message
- Shows a friendly inline message for backend errors (e.g. rate limits)
  instead of a raw fetch failure

## Running it

### Backend

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

### Frontend

```
cd frontend
npm install
npm run dev
```

Opens on `http://localhost:5173`. Needs the backend running on port 8000 at
the same time (CORS is wide open for local dev).

### API directly, without the frontend

Non-streaming, simplest for quick tests:
```
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a budget trip from Delhi to Goa, 1 to 7 May 2027", "thread_id": "test1"}'
```

If the agent decides to book something, this responds with
`{"status": "confirmation_required", "pending_action": {...}}` instead of a
normal answer. Approve or deny it with:
```
curl -X POST http://localhost:8000/confirm \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "test1", "approved": true}'
```

Streaming versions of both exist at `/chat/stream` and `/confirm/stream`,
returning Server-Sent Events instead of a single JSON blob — this is what
the frontend is built to eventually use (currently it still calls the
non-streaming endpoints; wiring it to the stream is a planned next step).

On Windows, PowerShell mangles inline JSON with curl, so write the payload
to a file first (put scratch test payloads under `backend/scratch/` —
that folder is gitignored):
```
'{"message": "...", "thread_id": "t1"}' | Out-File -Encoding utf8 scratch/body.json
curl.exe -N -X POST http://localhost:8000/chat/stream -H "Content-Type: application/json" -d "@scratch/body.json"
```

## Where this stands right now

Working end to end: multi-step reasoning over tools, live flight/hotel/
weather data, conversation memory that survives a restart, a prompt rule
against inventing exact numbers when a search comes back empty, a
budget-overrun warning rule, simulated booking with a real human-
confirmation gate, SSE streaming from the backend, a React frontend with a
proper confirm/decline UI, context trimming to survive Groq's free-tier
per-minute limit, and graceful handling of rate-limit errors instead of a
hard crash.

Known gaps / next steps:
- The frontend currently calls the non-streaming `/chat` and `/confirm`
  endpoints, not the SSE versions — so it waits for the full response
  rather than showing live reasoning steps.
- The frontend renders the agent's markdown as plain text — tables show up
  as raw `|` characters and literal `<br>` tags instead of being formatted.
  Needs a markdown renderer.
- Groq's free tier has a hard **daily** token cap (200,000/day) on top of
  the per-minute one — heavy testing can exhaust this for the rest of the
  day; trimming only helps with the per-minute limit, not this one.
- No systematic resilience testing beyond the rate-limit case (e.g. SerpApi
  hitting its 250/month cap, DuckDuckGo returning nothing, hasn't been
  deliberately tested).
- Not deployed anywhere yet — this all currently only runs locally.