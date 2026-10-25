"""Tests for reporting tools."""

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from line_ads_mcp.client import LineAdsClient
from line_ads_mcp.tools.reports import (
    _summarize_rows,
    get_daily_report,
    get_report,
    get_weekly_report,
)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A01887296807")


def test_summarize_rows():
    """Existing passing test updated to include new metrics and missing_metrics for cv."""
    summary = _summarize_rows(
        [
            {"impressions": 1000, "clicks": 50, "spend": 100.5},
            {"impressions": 500, "clicks": 10, "spend": 20},
        ]
    )

    assert summary == {
        "total_spend": 120.5,
        "total_clicks": 60,
        "total_impressions": 1500,
        "total_cv": 0,
        "conversion_events": {},
        "avg_ctr": 4.0,
        "avg_cpc": 2.01,
        "avg_cpm": 80.33,
        "missing_metrics": ["cv"],
    }


def test_summarize_rows_missing_metric_not_zero():
    """Missing metric is not treated as 0 silently; sums only present values and tags missing."""
    rows = [
        {"imp": 1000, "click": 50, "cost": 100.0, "cv": 5},
        {"imp": 500, "click": 10},  # cost and cv missing in this row
    ]
    summary = _summarize_rows(rows)

    assert summary["total_spend"] == 100.0
    assert summary["total_clicks"] == 60
    assert summary["total_impressions"] == 1500
    assert summary["total_cv"] == 5
    assert "cost" in summary["missing_metrics"] or "spend" in summary["missing_metrics"]
    assert "cv" in summary["missing_metrics"]


def test_summarize_rows_zero_denominators_return_none():
    """Zero impressions or clicks yield None for avg_ctr, avg_cpc, avg_cpm (not 0)."""
    rows = [{"imp": 0, "click": 0, "cost": 0.0, "cv": 0}]
    summary = _summarize_rows(rows)

    assert summary["avg_ctr"] is None
    assert summary["avg_cpc"] is None
    assert summary["avg_cpm"] is None
    assert "missing_metrics" not in summary


def test_summarize_rows_nested_statistics():
    """Extracts stats from nested statistics dict."""
    rows = [
        {
            "adId": "123",
            "statistics": {"imp": 2000, "click": 100, "cost": 300.0, "cv": 10},
        }
    ]
    summary = _summarize_rows(rows)

    assert summary["total_impressions"] == 2000
    assert summary["total_clicks"] == 100
    assert summary["total_spend"] == 300.0
    assert summary["total_cv"] == 10
    assert summary["avg_ctr"] == 5.0
    assert summary["avg_cpc"] == 3.0
    assert summary["avg_cpm"] == 150.0


@pytest.mark.asyncio
async def test_get_report_fetch_all_multipage(monkeypatch):
    """fetch_all=True fetches all pages and drops raw."""
    calls: list[tuple[str, dict[str, Any]]] = []

    async def fake_get(self, path: str, params: dict[str, Any] | None = None):
        calls.append((path, dict(params or {})))
        page = (params or {}).get("page", 1)
        if page == 1:
            return {
                "paging": {"page": 1, "size": 2, "totalElements": 3},
                "datas": [{"imp": 100, "click": 10, "cost": 20.0, "cv": 1}, {"imp": 200, "click": 20, "cost": 40.0, "cv": 2}],
            }
        return {
            "paging": {"page": 2, "size": 2, "totalElements": 3},
            "datas": [{"imp": 300, "click": 30, "cost": 60.0, "cv": 3}],
        }

    monkeypatch.setattr(LineAdsClient, "get", fake_get)

    result = await get_report("CAMPAIGN", "2026-05-01", "2026-05-07", page_size=2, fetch_all=True)

    assert result["ok"] is True
    data = result["data"]
    assert len(data["data"]) == 3
    assert data["report_level"] == "CAMPAIGN"
    assert data["date_range"] == {"start": "2026-05-01", "end": "2026-05-07"}
    assert data["date_basis"] == "UTC"
    assert data["by_day"] is False
    assert "raw" not in data
    assert data["paging"]["pages_fetched"] == 2
    assert data["paging"]["total_elements"] == 3
    assert data["paging"]["rows"] == 3
    assert data["paging"]["complete"] is True
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_get_report_single_request_mode(monkeypatch):
    """fetch_all=False performs single request and retains raw."""
    calls: list[tuple[str, dict[str, Any]]] = []

    async def fake_get(self, path: str, params: dict[str, Any] | None = None):
        calls.append((path, dict(params or {})))
        return {
            "paging": {"page": 1, "size": 100, "totalElements": 250},
            "datas": [{"imp": 100, "click": 10, "cost": 20.0, "cv": 1}],
        }

    monkeypatch.setattr(LineAdsClient, "get", fake_get)

    result = await get_report("CAMPAIGN", "2026-05-01", "2026-05-07", fetch_all=False, page_size=100)

    assert result["ok"] is True
    data = result["data"]
    assert len(data["data"]) == 1
    assert "raw" in data
    assert data["paging"]["pages_fetched"] == 1
    assert data["paging"]["total_elements"] == 250
    assert data["paging"]["complete"] is False  # 1 < 250
    assert len(calls) == 1
    assert calls[0][1]["page"] == 1
    assert calls[0][1]["size"] == 100


@pytest.mark.asyncio
async def test_get_report_by_day(monkeypatch):
    """by_day=True sends one request per calendar day, tags each row with date, drops raw."""
    calls: list[tuple[str, dict[str, Any]]] = []

    async def fake_get(self, path: str, params: dict[str, Any] | None = None):
        p = dict(params or {})
        calls.append((path, p))
        since = p.get("since")
        return {
            "paging": {"page": 1, "size": 100, "totalElements": 1},
            "datas": [{"imp": 100, "click": 5, "cost": 15.0, "cv": 1}],
        }

    monkeypatch.setattr(LineAdsClient, "get", fake_get)

    result = await get_report("CAMPAIGN", "2026-05-01", "2026-05-03", by_day=True)

    assert result["ok"] is True
    data = result["data"]
    assert data["by_day"] is True
    assert "raw" not in data
    assert len(calls) == 3
    assert calls[0][1]["since"] == "2026-05-01"
    assert calls[0][1]["until"] == "2026-05-01"
    assert calls[1][1]["since"] == "2026-05-02"
    assert calls[1][1]["until"] == "2026-05-02"
    assert calls[2][1]["since"] == "2026-05-03"
    assert calls[2][1]["until"] == "2026-05-03"

    rows = data["data"]
    assert len(rows) == 3
    assert rows[0]["date"] == "2026-05-01"
    assert rows[1]["date"] == "2026-05-02"
    assert rows[2]["date"] == "2026-05-03"

    paging = data["paging"]
    assert paging["complete"] is True
    assert paging["rows"] == 3
    assert len(paging["days"]) == 3
    assert paging["days"][0]["date"] == "2026-05-01"


@pytest.mark.asyncio
async def test_get_report_over_93_days_rejected():
    """Requesting >93 days with by_day=True is rejected."""
    result = await get_report("CAMPAIGN", "2026-01-01", "2026-05-01", by_day=True)

    assert result["ok"] is False
    assert "93" in result["message"]
    assert result.get("error_code") == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_get_report_end_before_start_rejected():
    """end_date < start_date is rejected."""
    result = await get_report("CAMPAIGN", "2026-05-10", "2026-05-01")

    assert result["ok"] is False
    assert "end_date" in result["message"]
    assert result.get("error_code") == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_get_report_yyyymmdd_date_formats(monkeypatch):
    """Accepts YYYYMMDD date strings."""
    calls: list[tuple[str, dict[str, Any]]] = []

    async def fake_get(self, path: str, params: dict[str, Any] | None = None):
        calls.append((path, dict(params or {})))
        return {"datas": []}

    monkeypatch.setattr(LineAdsClient, "get", fake_get)

    result = await get_report("CAMPAIGN", "20260501", "20260505", fetch_all=True)

    assert result["ok"] is True
    assert result["data"]["date_range"] == {"start": "2026-05-01", "end": "2026-05-05"}
    assert calls[0][1]["since"] == "2026-05-01"
    assert calls[0][1]["until"] == "2026-05-05"


@pytest.mark.asyncio
async def test_get_daily_report_defaults(monkeypatch):
    """get_daily_report defaults to level AD, yesterday UTC, and by_day=True."""
    calls: list[tuple[str, dict[str, Any]]] = []

    async def fake_get(self, path: str, params: dict[str, Any] | None = None):
        calls.append((path, dict(params or {})))
        return {"datas": []}

    monkeypatch.setattr(LineAdsClient, "get", fake_get)

    result = await get_daily_report()

    assert result["ok"] is True
    data = result["data"]
    assert data["report_level"] == "AD"
    assert data["by_day"] is True
    assert "/reports/online/ad" in calls[0][0]
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    assert data["date_range"] == {"start": yesterday, "end": yesterday}


@pytest.mark.asyncio
async def test_get_weekly_report_forwards_by_day(monkeypatch):
    """get_weekly_report covers last 7 full UTC days and forwards by_day."""
    calls: list[tuple[str, dict[str, Any]]] = []

    async def fake_get(self, path: str, params: dict[str, Any] | None = None):
        calls.append((path, dict(params or {})))
        return {"datas": []}

    monkeypatch.setattr(LineAdsClient, "get", fake_get)

    result = await get_weekly_report(level="CAMPAIGN", by_day=True)

    assert result["ok"] is True
    data = result["data"]
    assert data["report_level"] == "CAMPAIGN"
    assert data["by_day"] is True
    assert len(calls) == 7
    # 7 calls, one per day
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    assert data["date_range"] == {"start": seven_days_ago, "end": yesterday}


@pytest.mark.parametrize("total_cv", [0, 5])
def test_summary_event_counts_exclude_rates_values_duplicates_and_zeros(total_cv):
    summary = _summarize_rows([
        {"cv": total_cv, "cvViewItemDetail": "10", "cvPurchase": 2, "cvZero": 0,
         "cvrViewItemDetail": 0.5, "cpaViewItemDetail": 10,
         "cvViewItemDetailValue": 1000, "cvViewItemDetailWithEv": 40},
        {"statistics": {"cv": 0, "cvViewItemDetail": 19, "cvPurchase": 3,
                        "cvZero": 0, "cvNull": None, "cvValuePurchase": 500}},
    ])
    assert summary["total_cv"] == total_cv
    assert summary["conversion_events"] == {"cvViewItemDetail": 29, "cvPurchase": 5}
    assert ("cv_note" in summary) is (total_cv == 0)
    if total_cv == 0:
        assert summary["cv_note"] == "cv รวมเป็น 0 แต่มีคอนเวอร์ชันรายอีเวนต์ — อ่านคอลัมน์อีเวนต์ที่แคมเปญตั้งไว้ (เช่น cvViewItemDetail)"


def test_summary_event_no_double_count_across_nested_and_flat():
    summary = _summarize_rows([
        {"cv": 0, "cvPurchase": 3, "statistics": {"cvPurchase": 3}},
        {"cv": 0, "cvPurchase": None, "statistics": {"cvPurchase": 2}},
    ])
    assert summary["conversion_events"] == {"cvPurchase": 5}


@pytest.mark.parametrize("rows", [[], [{"cv": 0}], [{"cv": 0, "cvPurchase": 0}]])
def test_summary_no_cv_note_without_event_counts(rows):
    summary = _summarize_rows(rows)
    assert summary["conversion_events"] == {}
    assert "cv_note" not in summary


async def test_get_report_surfaces_conversion_events(monkeypatch):
    async def get(self, path, params=None):
        return {"datas": [{"campaignId": 123, "statistics": {"cv": 0, "cvViewItemDetail": 29}}]}

    monkeypatch.setattr(LineAdsClient, "get", get)
    result = await get_report("CAMPAIGN", "2026-10-01", "2026-10-25", fetch_all=False)
    assert result["ok"] is True
    assert result["data"]["summary"]["conversion_events"] == {"cvViewItemDetail": 29}
    assert result["data"]["summary"]["cv_note"]
