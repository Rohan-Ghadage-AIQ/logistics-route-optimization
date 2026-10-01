"""
Time Conversion & Normalization Utilities
Handles conversions between minutes-from-midnight, 24-hour HH:MM strings, and cross-midnight shifts.
"""
from typing import Union, Tuple
import datetime


def parse_time_to_minutes(val: Union[str, int, float, datetime.time, None], default: int = 0) -> int:
    """
    Parses various time representations into minutes from midnight (0 to 1440+).
    Supports:
      - Integers/Floats: 480 -> 480
      - Strings: "08:30:00", "08:30", "8:30 AM", "14:45"
      - datetime.time objects: time(8, 30) -> 510
    """
    if val is None:
        return default

    if isinstance(val, (int, float)):
        return int(val)

    if isinstance(val, datetime.time):
        return val.hour * 60 + val.minute

    if isinstance(val, datetime.datetime):
        return val.hour * 60 + val.minute

    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", ""):
        return default

    # If it's a numeric string like "480"
    if s.isdigit():
        return int(s)

    # Try standard time formats
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p", "%I %p"):
        try:
            dt = datetime.datetime.strptime(s, fmt)
            return dt.hour * 60 + dt.minute
        except ValueError:
            continue

    # Fallback to string splitting "HH:MM:SS" or "HH:MM"
    parts = s.split(":")
    if len(parts) >= 2:
        try:
            h = int(parts[0])
            m = int(parts[1])
            return h * 60 + m
        except ValueError:
            pass

    return default


def minutes_to_clock_str(minutes: int) -> str:
    """
    Converts minutes from midnight to a 24-hour 'HH:MM' string.
    Handles next-day times (> 1440).
    """
    if minutes is None:
        return "--:--"

    total_mins = int(minutes)
    days = total_mins // 1440
    rem = total_mins % 1440
    hours = rem // 60
    mins = rem % 60

    if days > 0:
        return f"{hours:02d}:{mins:02d} (+{days}D)"
    return f"{hours:02d}:{mins:02d}"


def normalize_shift(start_min: int, end_min: int) -> Tuple[int, int]:
    """
    Normalizes shifts that cross midnight.
    e.g. 20:00 (1200) to 02:00 (120) -> (1200, 1560)
    """
    if end_min < start_min:
        end_min += 1440
    return start_min, end_min
