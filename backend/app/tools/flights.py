import os

from langchain_core.tools import tool
from serpapi import GoogleSearch


@tool
def search_flights(origin: str, destination: str, departure_date: str, adults: int = 1) -> str:
    """
    Search one-way flight options between two airports using IATA codes
    (e.g. DEL for Delhi, GOI for Goa). departure_date must be YYYY-MM-DD.
    Returns up to 5 offers with airline, duration, and price (INR).
    """
    params = {
        "engine": "google_flights",
        "departure_id": origin.upper(),
        "arrival_id": destination.upper(),
        "outbound_date": departure_date,
        "type": "2",  # one-way
        "currency": "INR",
        "hl": "en",
        "api_key": os.getenv("SERPAPI_API_KEY"),
    }
    try:
        results = GoogleSearch(params).get_dict()
        if "error" in results:
            return f"Flight search failed: {results['error']}"

        offers = (results.get("best_flights") or []) + (results.get("other_flights") or [])
        if not offers:
            return "No flight offers found for this route/date."

        lines = []
        for offer in offers[:5]:
            price = offer.get("price", "N/A")
            duration_min = offer.get("total_duration")
            duration = f"{duration_min // 60}h{duration_min % 60}m" if duration_min else "N/A"
            legs = offer.get("flights", [])
            airline = legs[0]["airline"] if legs else "Unknown"
            lines.append(f"{airline} — {duration} — ₹{price}")
        return "\n".join(lines)
    except Exception as e:
        return f"Flight search failed: {e}"
