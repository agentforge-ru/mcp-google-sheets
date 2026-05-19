"""Smoke tests for mcp_google_sheets. These verify the package imports cleanly
and the safety guards behave as documented. Real API calls are NOT exercised here —
they would require a service-account JSON, which CI doesn't have."""
from __future__ import annotations

import pytest

from mcp_google_sheets.server import SafetyError, _check_safe_range


def test_package_imports():
    """Package imports without errors and exposes __version__."""
    import mcp_google_sheets

    assert mcp_google_sheets.__version__


# --- whole-column safety guard --------------------------------------------

@pytest.mark.parametrize(
    "bad_range",
    [
        "Sheet1!A:Z",
        "Data!A:A",
        "AnotherSheet!B:F",
    ],
)
def test_safety_rejects_whole_column_ranges(bad_range: str):
    """update_range must refuse ranges without row bounds."""
    with pytest.raises(SafetyError):
        _check_safe_range(bad_range)


@pytest.mark.parametrize(
    "ok_range",
    [
        "Sheet1!A1:Z100",
        "Data!A2:C10",
        "Sheet1!A1:A100",
        "MySheet!B5:F500",
    ],
)
def test_safety_accepts_bounded_ranges(ok_range: str):
    """Ranges with row bounds are allowed."""
    _check_safe_range(ok_range)  # no exception


def test_safety_accepts_single_cell():
    """Single-cell range is fine."""
    _check_safe_range("Sheet1!A1")
