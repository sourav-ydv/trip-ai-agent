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
- **Orchestration**: LangGraph's `create_react_agent` with a `MemorySaver`
  checkpointer, so a conversation thread remembers what's already been said

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

## Where this stands right now

Working: multi-step reasoning over tools, live flight/hotel/weather data,
conversation memory per thread, and a prompt rule that stops the model from
inventing exact train numbers or hotel names when a search comes back empty.

Not done yet: no booking-confirmation step (it only searches/estimates right
now, doesn't simulate an actual booking), no streaming of the reasoning trace
to a frontend, no persistent storage — `MemorySaver` is in-process only, so a
restart clears every conversation. There's also no frontend yet; this is
backend/API only for now.