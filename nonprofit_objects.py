from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class NonprofitObject:
    kind: str
    object_key: str
    created_at: datetime


def should_expire(item: NonprofitObject, now: datetime, ttl_days: int = 30) -> bool:
    age = now.astimezone(timezone.utc) - item.created_at.astimezone(timezone.utc)
    return age.days >= ttl_days


def lifecycle_rule(ttl_days: int = 30) -> dict[str, object]:
    return {"id": "throwaway-nonprofit-objects", "status": "Enabled", "expiration": {"days": ttl_days}}
