from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class TripPreferences(TypedDict, total=False):
    origin: str
    destination: str
    start_date: str
    end_date: str
    budget: str
    travel_mode_pref: str 


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
