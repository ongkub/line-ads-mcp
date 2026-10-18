"""Spend cap decisions use reports only, with no mutations or real network."""

import pytest

from line_ads_mcp.client import LineAdsClient
from line_ads_mcp.tools import spend_caps


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden_request(*args, **kwargs):
        pytest.fail("Unexpected HTTP request")

    monkeypatch.setattr(LineAdsClient, "request", forbidden_request)


@pytest.fixture
def report_stub(monkeypatch):
    def install(spend, complete=True, reason=None, rows=None):
        calls = []

        async def fake_report(**kwargs):
            calls.append(kwargs)
            return {
                "ok": True,
                "data": {
                    "summary": {"total_spend": spend},
                    "paging": {"complete": complete, "reason": reason},
                    "data": rows or [],
                },
            }

        monkeypatch.setattr(spend_caps, "get_report", fake_report)
        return calls

    return install


@pytest.mark.parametrize(
    "spend,complete,expected",
    [
        (101, True, "exceeded"),
        (100, True, "within_cap"),
        (75, True, "within_cap"),
        (75, False, "indeterminate"),
        (100, False, "indeterminate"),
        (101, False, "exceeded"),
        (75, None, "indeterminate"),
    ],
)
async def test_status_and_report_arguments(report_stub, spend, complete, expected):
    calls = report_stub(spend, complete, "max_pages_reached")
    result = await spend_caps.check_spend_cap(
        100, "2026-10-01", "2026-10-10", campaign_id="C1", ad_account_id="A1"
    )
    assert result["ok"] is True
    data = result["data"]
    assert data["status"] == expected
    assert data["spend"] == spend
    assert data["cap"] == 100
    assert data["difference"] == spend - 100
    assert data["percent_of_cap"] == spend
    assert data["data_complete"] is (complete is True)
    assert data["campaign_id"] == "C1"
    assert data["date_range"] == {"start": "2026-10-01", "end": "2026-10-10"}
    assert data["date_basis"] == "UTC"
    assert data["cost_unit_note"] == "ค่า cost จากรายงาน LINE Ads (สมมติเป็นบาท — ยืนยันกับบัญชีจริงก่อนเผยแพร่)"
    assert "projection" not in data
    if complete is not True:
        assert data["reason"] == "max_pages_reached"
    assert calls == [{
        "level": "CAMPAIGN", "start_date": "2026-10-01", "end_date": "2026-10-10",
        "campaign_id": "C1", "ad_account_id": "A1", "fetch_all": True,
    }]


async def test_float_edge_does_not_exceed(report_stub):
    report_stub(0.1 + 0.2)
    data = (await spend_caps.check_spend_cap(0.3, "2026-10-01", "2026-10-01"))["data"]
    assert data["status"] == "within_cap"
    assert data["spend"] == 0.3
    assert data["difference"] == 0
    assert data["percent_of_cap"] == 100


async def test_breakdown_and_summary_source(report_stub):
    report_stub(80.25, rows=[
        {"campaignId": "C1", "campaignName": "First", "statistics": {"cost": "30.15"}},
        {"campaignId": "C2", "name": "Second", "cost": 20.10},
        {"campaign_id": "C3", "name": "Legacy", "spend": 10},
        {"id": "C4", "name": "Missing cost"},
    ])
    data = (await spend_caps.check_spend_cap(100, "2026-10-01", "2026-10-10"))["data"]
    # The decision must use summary.total_spend, rather than a fresh row sum.
    assert data["spend"] == 80.25
    assert data["difference"] == -19.75
    assert data["percent_of_cap"] == 80.25
    assert data["campaign_id"] is None
    assert data["per_campaign"] == [
        {"campaign_id": "C1", "name": "First", "spend": 30.15},
        {"campaign_id": "C2", "name": "Second", "spend": 20.10},
        {"campaign_id": "C3", "name": "Legacy", "spend": 10.0},
        {"campaign_id": "C4", "name": "Missing cost", "spend": None},
    ]


@pytest.mark.parametrize("cap", [0, -1, float("nan"), float("inf"), -float("inf"), "invalid", None])
async def test_invalid_cap_rejected_before_report(report_stub, cap):
    calls = report_stub(0)
    result = await spend_caps.check_spend_cap(cap, "2026-10-01", "2026-10-10")
    assert result["ok"] is False
    assert result["error_code"] == "VALIDATION_ERROR"
    assert calls == []


@pytest.mark.parametrize(
    "cap,end,period_end,projected,status",
    [
        (200, "2026-10-02", "2026-10-05", 250, "exceeded"),
        (250, "2026-10-02", "2026-10-05", 250, "within_cap"),
        (300, "2026-10-02", "2026-10-05", 250, "within_cap"),
        (100, "2026-10-01", "2026-10-01", 100, "within_cap"),
    ],
)
async def test_projection_inclusive_days(report_stub, cap, end, period_end, projected, status):
    report_stub(100)
    data = (await spend_caps.check_spend_cap(cap, "2026-10-01", end, period_end=period_end))["data"]
    projection = data["projection"]
    assert projection["projected_spend"] == projected
    assert projection["projected_status"] == status
    assert projection["formula"] == "spend ÷ วันที่ผ่านไป × วันทั้งงวด"
    assert projection["is_estimate"] is True
    assert "ค่าประมาณ" in projection["note"]


async def test_partial_projection_keeps_indeterminate_and_reason(report_stub):
    report_stub(30, complete=False, reason="max_pages_reached")
    data = (await spend_caps.check_spend_cap(
        100, "2026-10-01", "2026-10-02", period_end="2026-10-10"
    ))["data"]
    assert data["status"] == "indeterminate"
    assert data["reason"] == "max_pages_reached"
    assert data["projection"]["projected_spend"] == 150
    assert data["projection"]["projected_status"] == "exceeded"
    assert data["projection"]["is_estimate"] is True


@pytest.mark.parametrize("period_end", ["2026-09-30", "2026-02-30", "20261010", "2026-1-1", "wrong", ""])
async def test_invalid_period_end(report_stub, period_end):
    calls = report_stub(100)
    result = await spend_caps.check_spend_cap(100, "2026-10-01", "2026-10-10", period_end=period_end)
    assert result["ok"] is False
    assert result["error_code"] == "VALIDATION_ERROR"
    assert calls == []


@pytest.mark.parametrize("start,end", [("wrong", "2026-10-10"), ("2026-10-10", "2026-10-01")])
async def test_invalid_report_dates(report_stub, start, end):
    calls = report_stub(0)
    result = await spend_caps.check_spend_cap(100, start, end)
    assert result["error_code"] == "VALIDATION_ERROR"
    assert calls == []


async def test_compact_report_dates_and_incomplete_fallback(report_stub):
    report_stub(0, complete=None)
    data = (await spend_caps.check_spend_cap(100, "20261001", "20261010"))["data"]
    assert data["date_range"] == {"start": "2026-10-01", "end": "2026-10-10"}
    assert data["status"] == "indeterminate"
    assert data["reason"]


async def test_report_error_passthrough(monkeypatch):
    error = {"ok": False, "status_code": 403, "error_code": "FORBIDDEN", "message": "denied"}

    async def fake_report(**kwargs):
        return error

    monkeypatch.setattr(spend_caps, "get_report", fake_report)
    assert await spend_caps.check_spend_cap(100, "2026-10-01", "2026-10-10") is error


async def test_real_report_path_is_get_only(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A01887296807")
    calls = []
    posts = []

    async def fake_request(self, method, path, **kwargs):
        calls.append((method, path, kwargs))
        assert method == "GET"
        page = kwargs["params"]["page"]
        rows = (
            [{"campaignId": f"C{i}", "campaignName": f"Campaign {i}", "cost": 0.6} for i in range(100)]
            if page == 1 else [{"campaignId": "C100", "campaignName": "Last", "cost": 60}]
        )
        return {
            "paging": {"page": page, "size": 100, "totalElements": 101},
            "datas": rows,
        }

    async def forbidden_post(*args, **kwargs):
        posts.append((args, kwargs))
        pytest.fail("Spend cap checks must never POST")

    monkeypatch.setattr(LineAdsClient, "request", fake_request)
    monkeypatch.setattr(LineAdsClient, "post", forbidden_post)
    result = await spend_caps.check_spend_cap(100, "2026-10-01", "2026-10-10", campaign_id="C1")
    assert result["ok"] is True
    assert result["data"]["status"] == "exceeded"
    assert result["data"]["spend"] == 120
    assert result["data"]["data_complete"] is True
    assert len(result["data"]["per_campaign"]) == 101
    assert [call[2]["params"]["page"] for call in calls] == [1, 2]
    assert all(call[1] == "/adaccounts/A01887296807/reports/online/campaign" for call in calls)
    assert all(call[2]["params"]["campaignId"] == "C1" for call in calls)
    assert posts == []


async def test_missing_cost_rows_are_indeterminate(monkeypatch):
    async def fake_report(**kwargs):
        return {
            "ok": True,
            "data": {
                "summary": {"total_spend": 80, "missing_metrics": ["cost"]},
                "paging": {"complete": True, "reason": None},
                "data": [{"campaign": {"id": 1, "name": "ก"}, "statistics": {"cost": 80}}, {"campaign": {"id": 2}}],
            },
        }

    monkeypatch.setattr(spend_caps, "get_report", fake_report)
    result = await spend_caps.check_spend_cap(100, "2026-10-01", "2026-10-07")
    data = result["data"]
    assert data["status"] == "indeterminate"
    assert data["data_complete"] is False
    assert "cost" in data["reason"]
    assert data["per_campaign"][0] == {"campaign_id": 1, "name": "ก", "spend": 80.0}
    assert data["per_campaign"][1]["spend"] is None


async def test_missing_cost_still_exceeded_when_partial_spend_above_cap(monkeypatch):
    async def fake_report(**kwargs):
        return {"ok": True, "data": {"summary": {"total_spend": 120, "missing_metrics": ["cost"]}, "paging": {"complete": True}, "data": []}}

    monkeypatch.setattr(spend_caps, "get_report", fake_report)
    result = await spend_caps.check_spend_cap(100, "2026-10-01", "2026-10-07")
    assert result["data"]["status"] == "exceeded"
