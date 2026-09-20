from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def book_flight(airline: str, price: str, origin: str, destination: str, date: str) -> str:
    """
    Simulate booking a specific flight (SIMULATED — no real payment or ticket
    is issued). Call this only once the user has explicitly agreed on one
    specific flight from search_flights results — not as a way to check
    availability. This always pauses for human confirmation before completing.
    """
    decision = interrupt(
        {
            "action": "book_flight",
            "details": f"{airline} — {origin} to {destination} on {date} — {price}",
        }
    )
    if decision.get("approved"):
        return f"SIMULATED booking confirmed: {airline}, {origin}->{destination} on {date}, {price}."
    return "Booking cancelled — user did not approve."


@tool
def book_hotel(name: str, price: str, check_in: str, check_out: str) -> str:
    """
    Simulate booking a specific hotel (SIMULATED — no real payment or
    reservation is made). Call this only once the user has explicitly agreed
    on one specific hotel from search_hotels results. Always pauses for
    human confirmation before completing.
    """
    decision = interrupt(
        {
            "action": "book_hotel",
            "details": f"{name} — {check_in} to {check_out} — {price}",
        }
    )
    if decision.get("approved"):
        return f"SIMULATED booking confirmed: {name}, {check_in} to {check_out}, {price}."
    return "Booking cancelled — user did not approve."