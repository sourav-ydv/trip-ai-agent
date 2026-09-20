from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

_search = DuckDuckGoSearchRun()


@tool
def search_web(query: str) -> str:
    """
    General-purpose web search — no API key required. Use this for anything
    with no dedicated tool: top attractions in a city, train options (there is
    no free public train-booking API), local events, or other factual lookups
    needed to plan the trip.
    """
    try:
        return _search.run(query)
    except Exception as e:
        return f"Web search failed: {e}"
