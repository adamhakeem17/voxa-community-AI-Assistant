from enum import StrEnum

class BookingDecision(StrEnum):
    AUTO = "auto"
    HUMAN = "human"
    DENY = "deny"

def booking_decision(party_size: int, max_auto: int = 8) -> BookingDecision:
    if party_size <= 0:
        return BookingDecision.DENY
    if party_size <= max_auto:
        return BookingDecision.AUTO
    return BookingDecision.HUMAN
