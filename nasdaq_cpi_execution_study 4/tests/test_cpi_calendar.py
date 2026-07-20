"""
Bare-minimum tests for cpi_calendar.py — enough to catch a broken date
list or a timezone regression, not an exhaustive calendar audit.
"""
from datetime import date

from cpi_study.cpi_calendar import load_cpi_calendar, releases_between


def test_known_release_is_present():
    """The Jan 11, 2024 CPI release (used elsewhere to validate dataset
    timestamps) must actually be in the calendar."""
    calendar = load_cpi_calendar()
    release_dates = {ev.release_date for ev in calendar}
    assert date(2024, 1, 11) in release_dates


def test_releases_are_8_30_et():
    calendar = load_cpi_calendar()
    for ev in calendar[:5]:
        assert ev.release_dt_et.hour == 8
        assert ev.release_dt_et.minute == 30


def test_releases_between_filters_correctly():
    events = releases_between("2024-01-01", "2024-03-31")
    assert len(events) == 3  # Jan, Feb, Mar 2024 releases
    for ev in events:
        assert date(2024, 1, 1) <= ev.release_date <= date(2024, 3, 31)
