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
  requiring an explicit approve/deny via a `/confirm` endpoint before
  completing — one pause per booking action, so a round-trip needs two
  separate confirmations

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

Hit it with:
```
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a budget trip from Delhi to Goa, 1 to 7 May 2027", "thread_id": "test1"}'
```

Keep using the same `thread_id` to continue a planning session.

If the agent decides to book something, `/chat` responds with
`{"status": "confirmation_required", "pending_action": {...}}` instead of a
normal answer. Approve or deny it with:
```
curl -X POST http://localhost:8000/confirm \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "test1", "approved": true}'
```


## Where this stands right now

Working: multi-step reasoning over tools, live flight/hotel/weather data,
conversation memory that survives a restart (SQLite-backed checkpointer), and
a prompt rule that stops the model from inventing exact train numbers or
hotel names when a search comes back empty. Simulated flight/hotel booking
now has a real human-confirmation gate before anything "completes."

Not done yet: no streaming of the reasoning trace to a frontend, no
frontend at all yet — this is backend/API only for now. `/chat` and
`/confirm` both currently return a `trace` field with the full message
history for debugging; that'll come out once there's a frontend that
visualizes it properly instead.