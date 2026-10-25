"""
Time Systems & Epoch Management
===============================
Provides conversions between Mission Elapsed Time (MET), UTC Gregorian strings,
Julian Date (JD), and Modified Julian Date (MJD).
"""

from datetime import datetime, timezone, timedelta
import math

# Mission Launch Epoch: 28 Sep 2026 14:00:00 UTC (T0 = 0.0s)
DEFAULT_MISSION_EPOCH = datetime(2026, 9, 28, 14, 0, 0, tzinfo=timezone.utc)

def parse_iso_epoch(epoch_str: str) -> datetime:
    """Parses an ISO 8601 UTC timestamp into a timezone-aware datetime."""
    clean_str = epoch_str.replace("Z", "+00:00")
    return datetime.fromisoformat(clean_str)

def format_iso_epoch(dt: datetime) -> str:
    """Formats a datetime into a standard ISO 8601 UTC string."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def format_gmat_utc(dt: datetime) -> str:
    """Formats datetime to NASA GMAT UTCGregorian format (e.g. '28 Sep 2026 14:08:42.350')."""
    return dt.astimezone(timezone.utc).strftime("%d %b %Y %H:%M:%S.%f")[:-3]

format_gmat_epoch = format_gmat_utc


def datetime_to_julian_date(dt: datetime) -> float:
    """
    Computes Julian Date (JD) from a timezone-aware datetime.
    Standard astronomical algorithm (Vallado, 2013).
    """
    utc_dt = dt.astimezone(timezone.utc)
    year = utc_dt.year
    month = utc_dt.month
    day = utc_dt.day
    hour = utc_dt.hour
    minute = utc_dt.minute
    second = utc_dt.second + utc_dt.microsecond * 1e-6

    if month <= 2:
        year -= 1
        month += 12

    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)

    jd_day = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + b - 1524.5
    jd_fraction = (hour + (minute + second / 60.0) / 60.0) / 24.0

    return jd_day + jd_fraction

def julian_date_to_mjd(jd: float) -> float:
    """Converts Julian Date to Modified Julian Date (MJD)."""
    return jd - 2400000.5

def elapsed_seconds_to_datetime(elapsed_s: float, epoch: datetime = DEFAULT_MISSION_EPOCH) -> datetime:
    """Computes UTC datetime from mission elapsed seconds."""
    return epoch + timedelta(seconds=elapsed_s)

def datetime_to_elapsed_seconds(dt: datetime, epoch: datetime = DEFAULT_MISSION_EPOCH) -> float:
    """Computes mission elapsed seconds from a UTC datetime."""
    return (dt - epoch).total_seconds()
