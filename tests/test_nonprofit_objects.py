from datetime import datetime, timezone, timedelta

from nonprofit_objects import NonprofitObject, should_expire


def test_old_donor_receipt_expires_but_recent_volunteer_reminder_stays() -> None:
    now = datetime(2026, 10, 24, tzinfo=timezone.utc)
    receipt = NonprofitObject("donor_receipt", "receipts/2026/old.json", now - timedelta(days=31))
    reminder = NonprofitObject("volunteer_reminder", "reminders/next-week.json", now - timedelta(days=3))

    assert should_expire(receipt, now) is True
    assert should_expire(reminder, now) is False
