from voxa.policy import BookingDecision, booking_decision

def test_standard_booking():
    assert booking_decision(8) == BookingDecision.AUTO

def test_large_group():
    assert booking_decision(9) == BookingDecision.HUMAN
    assert booking_decision(40) == BookingDecision.HUMAN

def test_invalid():
    assert booking_decision(0) == BookingDecision.DENY
