"""
cpi_calendar.py
================
Ground-truth calendar of U.S. CPI release dates and times.

All CPI releases occur at 8:30 AM Eastern Time. Dates below are sourced from:
  - U.S. Bureau of Labor Statistics, Schedule of Releases for the CPI
    (https://www.bls.gov/schedule/news_release/cpi.htm)
  - ALFRED (Archival FRED), Federal Reserve Bank of St. Louis, Release ID 10
    (https://alfred.stlouisfed.org/release/downloaddates?rid=10)

These are the actual historical publication dates, not estimated. Where BLS
listed more than one revision date in a given month, the primary headline
release date (the one associated with the scheduled monthly report) is used.

Note: The October 2025 CPI release was delayed to 2025-10-24 and the
scheduled November 2025 release did not occur on its usual date because of
the 2025 lapse in federal appropriations; the November 2025 report was
folded into the December 18, 2025 release. This is reflected below.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date, time
import zoneinfo

ET = zoneinfo.ZoneInfo("America/New_York")
CPI_RELEASE_TIME = time(8, 30)  # 8:30 AM ET, every release


@dataclass(frozen=True)
class CPIRelease:
    reference_month: str   # e.g. "2024-01" -> the month the data describes
    release_date: date     # calendar date the report was published
    release_dt_et: datetime  # tz-aware timestamp of the release (8:30 ET)


# Primary headline CPI release dates, 2019-01 through 2026-06 (reference month
# is the month prior to the release date in the normal case).
_RELEASE_DATES: list[str] = [
    "2019-01-11", "2019-02-13", "2019-03-12", "2019-04-10", "2019-05-10",
    "2019-06-12", "2019-07-11", "2019-08-13", "2019-09-12", "2019-10-10",
    "2019-11-13", "2019-12-11",
    "2020-01-14", "2020-02-13", "2020-03-11", "2020-04-10", "2020-05-12",
    "2020-06-10", "2020-07-14", "2020-08-12", "2020-09-11", "2020-10-13",
    "2020-11-12", "2020-12-10",
    "2021-01-13", "2021-02-10", "2021-03-10", "2021-04-13", "2021-05-12",
    "2021-06-10", "2021-07-13", "2021-08-11", "2021-09-14", "2021-10-13",
    "2021-11-10", "2021-12-10",
    "2022-01-12", "2022-02-10", "2022-03-10", "2022-04-12", "2022-05-11",
    "2022-06-10", "2022-07-13", "2022-08-10", "2022-09-13", "2022-10-13",
    "2022-11-10", "2022-12-13",
    "2023-01-12", "2023-02-14", "2023-03-14", "2023-04-12", "2023-05-10",
    "2023-06-13", "2023-07-12", "2023-08-10", "2023-09-13", "2023-10-12",
    "2023-11-14", "2023-12-12",
    "2024-01-11", "2024-02-13", "2024-03-12", "2024-04-10", "2024-05-15",
    "2024-06-12", "2024-07-11", "2024-08-14", "2024-09-11", "2024-10-10",
    "2024-11-13", "2024-12-11",
    "2025-01-15", "2025-02-12", "2025-03-12", "2025-04-10", "2025-05-13",
    "2025-06-11", "2025-07-15", "2025-08-12", "2025-09-11", "2025-10-24",
    "2025-12-18",  # combined Nov 2025 release, delayed due to shutdown
    "2026-01-13", "2026-02-13", "2026-03-11", "2026-04-10", "2026-05-12",
    "2026-06-10",
]


def _reference_month_for(release_dt: date) -> str:
    """CPI released on date D normally describes the prior calendar month."""
    year, month = release_dt.year, release_dt.month
    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{month - 1:02d}"


def load_cpi_calendar() -> list[CPIRelease]:
    """Return the full list of CPIRelease events, sorted chronologically."""
    events = []
    for d_str in _RELEASE_DATES:
        d = datetime.strptime(d_str, "%Y-%m-%d").date()
        dt_et = datetime.combine(d, CPI_RELEASE_TIME, tzinfo=ET)
        events.append(CPIRelease(
            reference_month=_reference_month_for(d),
            release_date=d,
            release_dt_et=dt_et,
        ))
    return sorted(events, key=lambda e: e.release_date)


def releases_between(start: str, end: str) -> list[CPIRelease]:
    """Filter releases to a date range, inclusive. start/end as 'YYYY-MM-DD'."""
    s = datetime.strptime(start, "%Y-%m-%d").date()
    e = datetime.strptime(end, "%Y-%m-%d").date()
    return [ev for ev in load_cpi_calendar() if s <= ev.release_date <= e]


if __name__ == "__main__":
    cal = load_cpi_calendar()
    print(f"Loaded {len(cal)} CPI release events "
          f"({cal[0].release_date} to {cal[-1].release_date})")
    for ev in cal[-5:]:
        print(ev)
