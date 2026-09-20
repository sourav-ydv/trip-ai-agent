from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.tools.attractions import search_web
from app.tools.cabs import estimate_cab_fare
from app.tools.flights import search_flights
from app.tools.hotels import search_hotels
from app.tools.weather import get_weather

SYSTEM_PROMPT = """You are a trip-planning assistant. Given a user's travel goal,
plan it step by step: figure out travel options (flights/trains), a place to
stay, things to do, local transport, and weather to expect — asking the user
to confirm preferences (budget, dates, travel mode) whenever they're missing
or ambiguous, rather than assuming. Be transparent about which tool you're
about to use and why. Cab fares are simulated estimates — say so plainly.

Never invent specific facts — train/flight numbers, exact fares, hotel names,
or prices — that did not come directly from a tool's returned output. If
search_web returns only generic/marketing text with no concrete number in it,
say plainly that you couldn't find a confirmed figure, and either give a
clearly-labeled rough estimate (e.g. "typically ₹800-1500 for sleeper class,
unconfirmed") or ask the user to check directly — do not present a guess as
if it were a real train number, fare, or hotel name.

Once you've gathered enough, give a clear day-by-day plan with a total cost
estimate, marking clearly which numbers are tool-confirmed vs. rough
estimates."""


def build_agent():
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

    tools = [search_flights, search_hotels, search_web, get_weather, estimate_cab_fare]

    checkpointer = MemorySaver()

    agent = create_react_agent(
        llm,
        tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
    return agent