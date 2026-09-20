import os

from langchain_core.tools import tool
from serpapi import GoogleSearch


@tool
def search_hotels(city: str, check_in: str, check_out: str, adults: int = 1) -> str:
    """
    Search hotel options in a city by name (e.g. "Goa", "Delhi").
    Dates must be YYYY-MM-DD. Returns up to 5 hotels with name and total price (INR).
    """
    params = {
        "engine": "google_hotels",
        "q": f"{city} hotels",
        "check_in_date": check_in,
        "check_out_date": check_out,
        "adults": adults,
        "currency": "INR",
        "hl": "en",
        "api_key": os.getenv("SERPAPI_API_KEY"),
    }
    try:
        results = GoogleSearch(params).get_dict()
        if "error" in results:
            return f"Hotel search failed: {results['error']}"

        properties = results.get("properties") or []
        if not properties:
            return "No hotel offers found for this city/dates."

        lines = []
        for hotel in properties[:5]:
            name = hotel.get("name", "Unknown")
            price = hotel.get("rate_per_night", {}).get("lowest", "N/A")
            lines.append(f"{name} — {price} per night")
        return "\n".join(lines)
    except Exception as e:
        return f"Hotel search failed: {e}"