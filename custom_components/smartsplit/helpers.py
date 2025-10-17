
from __future__ import annotations
from datetime import datetime

def is_night(now: datetime) -> bool:
    h = now.hour
    return h >= 22 or h < 6

def clamp(v, lo, hi):
    return max(lo, min(hi, v))
