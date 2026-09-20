from langchain_core.tools import tool


@tool
def estimate_cab_fare(distance_km: float, city_tier: str = "tier1") -> str:
    """
    Estimate local cab/scooter cost for a given distance in km. This is a
    SIMULATED estimate — no free public cab-booking API exists — so use it to
    give the user a rough local-travel budget line, not an actual booking.
    """
    rate_per_km = 12 if city_tier == "tier1" else 8
    base_fare = 50
    estimate = base_fare + distance_km * rate_per_km
    return (
        f"Estimated fare for {distance_km} km: ~₹{estimate:.0f} "
        "(simulated estimate, not a real booking)"
    )
