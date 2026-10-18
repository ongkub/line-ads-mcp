"""Chapter-level workflow scenarios using an in-memory LINE Ads API."""
import csv
from datetime import date, timedelta

import pytest

from line_ads_mcp.client import LineAdsClient
from line_ads_mcp.tools.ads import create_ad, get_ad_status, pause_ad
from line_ads_mcp.tools.adsets import create_adset, list_adsets, update_adset
from line_ads_mcp.tools.audiences import create_audience, list_audiences
from line_ads_mcp.tools.campaigns import create_campaign, list_campaigns
from line_ads_mcp.tools.csv_sync import sync_ad_daily_csv
from line_ads_mcp.tools.reach import estimate_adset_reach
from line_ads_mcp.tools.reports import get_daily_report, get_report
from line_ads_mcp.tools.spend_caps import check_spend_cap


@pytest.fixture
def fake_api(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A01887296807")
    monkeypatch.delenv("LINE_ADS_WORKSPACE_DIR", raising=False)
    state = {
        "calls": [], "campaigns": [{"id": "c1", "configuredStatus": "ACTIVE"}],
        "adgroups": [{"id": "s1", "configuredStatus": "ACTIVE", "dailyBudgetMicro": 100_000_000}],
        "ads": [{"id": "a1", "adgroupId": "s1", "configuredStatus": "ACTIVE", "deliveryStatus": "NOT_APPROVED"}],
        "audiences": [{"id": "ready", "name": "Ready", "status": "READY", "estimatedAudienceSize": 5000},
                      {"id": "pending", "status": "IN_PROGRESS"}],
        "report_rows": [{"ad": {"id": "a1", "name": "Ad"}, "campaign": {"id": "c1"}, "adgroup": {"id": "s1"},
                         "imp": 100, "click": 10, "cost": 50, "cv": 2}],
        "ars": {"uuid": "sim1", "reach": [1000, 2000], "result": [20, 40]},
    }

    async def get(self, path, params=None):
        params = params or {}
        state["calls"].append(("GET", path, dict(params)))
        collection = "audiences" if path.endswith("/custom-audiences") else next((key for key in ("campaigns", "adgroups", "ads") if path.endswith("/" + key)), None)
        if "/reports/online/" in path:
            row = dict(state["report_rows"][0])
            if params.get("size") == 1:
                rows = [row] if params.get("page", 1) == 1 else [dict(row, imp=50, click=5, cost=25, cv=1)]
                return {"paging": {"page": params.get("page", 1), "size": 1, "totalElements": 2}, "datas": rows}
            return {"paging": {"page": 1, "size": 100, "totalElements": 1}, "datas": [row]}
        if collection:
            records = state[collection]
            if collection != "audiences" and path.rstrip("/").split("/")[-2] == collection:
                ident = path.rstrip("/").split("/")[-1]
                records = [row for row in records if str(row.get("id")) == ident]
            return {"paging": {"page": 1, "size": 100, "totalElements": len(records)}, "datas": [dict(row) for row in records]}
        return {"paging": {"page": 1, "size": 100, "totalElements": 0}, "datas": []}

    async def post(self, path, body):
        state["calls"].append(("POST", path, body))
        if path.endswith("/simulation/ars"):
            return state["ars"]
        collection = next((key for key in ("campaigns", "adgroups", "ads") if path.endswith("/" + key)), None)
        if collection:
            ident = {"campaigns": "c-new", "adgroups": "s-new", "ads": "a-new"}[collection]
            state[collection].append(dict(body, id=ident, deliveryStatus="NOT_DELIVERING"))
            return {"id": ident}
        if any(path.endswith("/" + key + "/" + ident) for key, ident in (("adgroups", "s1"), ("ads", "a1"))):
            key = "adgroups" if "/adgroups/" in path else "ads"
            ident = path.split("/")[-1]
            row = next(r for r in state[key] if r["id"] == ident)
            row.update(body)
            return {"saved": True}
        return {"id": "aud-new"}

    monkeypatch.setattr(LineAdsClient, "get", get)
    monkeypatch.setattr(LineAdsClient, "post", post)
    return state


@pytest.mark.asyncio
async def test_ch1_campaign_builder(fake_api, tmp_path):
    audiences = await list_audiences()
    assert next(x for x in audiences["data"]["audiences"] if x["id"] == "ready")["usable_in_adset"] is True
    assert next(x for x in audiences["data"]["audiences"] if x["id"] == "pending")["usable_in_adset"] is False
    calls_before = len(fake_api["calls"])
    aud = await create_audience("Visitors", "WEBTRAFFIC", {"visitType": "VISIT_ALL", "retentionDays": 30})
    assert aud["dry_run"] and len(fake_api["calls"]) == calls_before
    c = await create_campaign("Campaign", "GAIN_FRIENDS", start_date="2026-10-20T00:00:00Z")
    s = await create_adset("c1", "Set", "CPF", "LOWEST_COST", "FRIEND", 100, custom_audience_ids=["ready"], excluded_audience_ids=["exclude"])
    ad = await create_ad("s1", "Ad", "hash", "Title", "ADD_FRIEND", campaign_id="c1")
    assert all(x["dry_run"] for x in (c, s, ad))
    assert s["payload"]["targeting"]["customAudienceIds"] == ["ready"]
    assert s["payload"]["targeting"]["excludedCustomAudienceIds"] == ["exclude"]
    assert not [call for call in fake_api["calls"] if call[0] == "POST"]
    made = await create_campaign("Campaign", "GAIN_FRIENDS", start_date="2026-10-20T00:00:00Z", dry_run=False, workspace_dir=str(tmp_path))
    assert made["readback_ok"] is True and made["readback"]["configured_status"] == "PAUSED"
    assert made["data"]["id"] == "c-new"
    assert (tmp_path / "line-ads-data" / "change_log.jsonl").exists()
    status = await get_ad_status("a1")
    assert status["data"]["delivery_status"] == "NOT_APPROVED"


@pytest.mark.asyncio
async def test_ch2_scheduled_reporting(fake_api, tmp_path):
    daily = await get_daily_report()
    assert daily["data"]["paging"]["complete"] is True
    paged = await get_report("AD", "2026-10-17", "2026-10-17", page_size=1)
    assert paged["data"]["paging"]["complete"] is True
    assert paged["data"]["paging"]["pages_fetched"] == 2
    async def reports(**kwargs):
        rows = [{"cost": 11}]
        return {"ok": True, "data": {"data": rows, "paging": {"complete": True}, "summary": {"total_spend": 11, "missing_metrics": []}}}
    from line_ads_mcp.tools import spend_caps
    original = spend_caps.get_report
    spend_caps.get_report = reports
    try:
        assert (await check_spend_cap(10, "2026-10-01", "2026-10-01"))["data"]["status"] == "exceeded"
        assert (await check_spend_cap(11, "2026-10-01", "2026-10-01"))["data"]["status"] == "within_cap"
        async def incomplete(**kwargs):
            out = await reports(**kwargs); out["data"]["paging"]["complete"] = False; return out
        spend_caps.get_report = incomplete
        assert (await check_spend_cap(12, "2026-10-01", "2026-10-01"))["data"]["status"] == "indeterminate"
    finally:
        spend_caps.get_report = original
    await sync_ad_daily_csv("2026-10-01", "2026-10-01", str(tmp_path), dry_run=False)
    await sync_ad_daily_csv("2026-10-01", "2026-10-01", str(tmp_path), dry_run=False)
    with open(tmp_path / "line-ads-data" / "ad_daily.csv", newline="", encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 1


@pytest.mark.asyncio
async def test_ch3_optimizer(fake_api):
    active = await list_campaigns(status="ACTIVE")
    assert [r["id"] for r in active["data"]["datas"]] == ["c1"]
    changed = await update_adset("s1", daily_budget=250, dry_run=False)
    assert changed["before"]["dailyBudgetMicro"] == 100_000_000
    assert changed["readback_ok"] is True
    assert changed["readback"]["dailyBudgetMicro"] == 250_000_000
    before = len(fake_api["calls"])
    assert (await pause_ad("a1"))["dry_run"] is True
    assert len(fake_api["calls"]) == before
    paused = await pause_ad("a1", dry_run=False)
    assert paused["readback_ok"] is True


@pytest.mark.asyncio
async def test_ch4_dashboard(fake_api):
    end = date(2026, 10, 18)
    start = end - timedelta(days=27)
    result = await get_report("AD", start.isoformat(), end.isoformat(), by_day=True)
    calls = [c for c in fake_api["calls"] if c[0] == "GET" and "/reports/online/" in c[1]]
    assert len(calls) == 28
    assert result["data"]["summary"]["total_clicks"] == 280
    assert result["data"]["summary"]["avg_ctr"] == 10.0
    assert {row["date"] for row in result["data"]["data"]} == {(start + timedelta(days=i)).isoformat() for i in range(28)}


@pytest.mark.asyncio
async def test_ch5_audience_advisor(fake_api):
    await list_adsets()
    await list_audiences()
    result = await estimate_adset_reach("c1", "GAIN_FRIENDS", 100, "CPF", "FRIEND", custom_audience_ids=["ready"], excluded_audience_ids=["excluded"])
    assert result["data"]["reach"] == {"min": 1000, "max": 2000}
    assert result["data"]["request"]["targeting"]["customAudienceIds"] == ["ready"]
    posts = [c[1] for c in fake_api["calls"] if c[0] == "POST"]
    assert posts == ["/adaccounts/A01887296807/simulation/ars"]


@pytest.mark.asyncio
async def test_ch6_planner(fake_api):
    await list_campaigns()
    await get_report("CAMPAIGN", "2026-10-17", "2026-10-17")
    assert all(call[0] == "GET" for call in fake_api["calls"])
    assert (await create_campaign("Plan", "GAIN_FRIENDS", start_date="2026-10-20T00:00:00Z"))["dry_run"]
    assert (await create_adset("c1", "Plan set", "CPF", "LOWEST_COST", "FRIEND", 100))["dry_run"]
    assert (await create_ad("s1", "Plan ad", "hash", "Title", "ADD_FRIEND", campaign_id="c1"))["dry_run"]
    assert all(call[0] == "GET" for call in fake_api["calls"])
