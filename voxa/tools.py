from datetime import datetime, timezone
from uuid import uuid4

from pipecat.services.llm_service import FunctionCallParams
from .business import BUSINESS
from .policy import BookingDecision, booking_decision

async def lookup_business_fact(params: FunctionCallParams, topic: str):
    """Look up a verified fact about the fictional demo restaurant.

    Args:
        topic: dogs, vegetarian, wheelchair, terrace, parking, or opening_hours.
    """
    topic = topic.strip().lower()
    if topic == "opening_hours":
        result = {"state": "known", "hours": BUSINESS["hours"], "source": "demo_config"}
    elif topic in BUSINESS["facts"]:
        result = {"state": "known", "answer": BUSINESS["facts"][topic], "source": "demo_config"}
    else:
        result = {"state": "unknown", "answer": None, "instruction": "Do not guess."}
    await params.result_callback(result)

async def check_demo_availability(params: FunctionCallParams, party_size: int, date: str, time: str):
    """Check fictional demo availability.

    Args:
        party_size: Number of guests.
        date: Requested date.
        time: Requested time.
    """
    decision = booking_decision(party_size, BUSINESS["automatic_booking_max_guests"])
    if decision != BookingDecision.AUTO:
        await params.result_callback({
            "available": False,
            "reason": "human_approval_required",
            "confirmed": False,
            "instruction": "Do not imply that this group is bookable automatically.",
        })
        return
    await params.result_callback({
        "available": True,
        "party_size": party_size,
        "date": date,
        "time": time,
        "alternatives": ["19:30", "20:30"],
        "demo_only": True,
    })

async def create_demo_reservation(
    params: FunctionCallParams,
    customer_name: str,
    party_size: int,
    date: str,
    time: str,
):
    """Create a fictional reservation.

    Args:
        customer_name: First name is sufficient.
        party_size: Number of guests.
        date: Requested date.
        time: Requested time.
    """
    decision = booking_decision(party_size, BUSINESS["automatic_booking_max_guests"])
    if decision != BookingDecision.AUTO:
        await params.result_callback({
            "status": "blocked",
            "confirmed": False,
            "reason": "human_approval_required",
            "instruction": "Never say this reservation is confirmed.",
        })
        return
    await params.result_callback({
        "status": "confirmed",
        "confirmed": True,
        "booking_id": f"DEMO-{uuid4().hex[:8].upper()}",
        "customer_name": customer_name,
        "party_size": party_size,
        "date": date,
        "time": time,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "demo_only": True,
    })

async def create_group_enquiry(
    params: FunctionCallParams,
    customer_name: str,
    party_size: int,
    date: str,
    time: str,
    notes: str = "",
):
    """Create a fictional staff-approval enquiry for a large party.

    Args:
        customer_name: First name.
        party_size: Number of guests.
        date: Requested date.
        time: Requested time.
        notes: Optional event notes.
    """
    decision = booking_decision(party_size, BUSINESS["automatic_booking_max_guests"])
    if decision != BookingDecision.HUMAN:
        await params.result_callback({"status": "not_needed", "confirmed": False})
        return
    await params.result_callback({
        "status": "pending_human_approval",
        "confirmed": False,
        "enquiry_id": f"GROUP-{uuid4().hex[:8].upper()}",
        "party_size": party_size,
        "date": date,
        "time": time,
        "notes": notes,
        "instruction": "Explicitly state that this is not confirmed.",
    })

async def allergy_safety_check(params: FunctionCallParams, question: str):
    """Handle allergy or cross-contamination safety questions.

    Args:
        question: Caller question.
    """
    await params.result_callback({
        "state": "human_required",
        "confirmed_safe": False,
        "instruction": "Never guarantee allergen safety or zero cross-contamination.",
    })
