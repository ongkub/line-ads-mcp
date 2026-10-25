"""Tests for reach simulation (ARS) tool."""

from typing import Any
import pytest

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient
from line_ads_mcp.tools.adsets import create_adset
from line_ads_mcp.tools.reach import NOTE_ARS, estimate_adset_reach


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A01887296807")


@pytest.mark.asyncio
async def test_estimate_adset_reach_body_shape_and_micro_conversion(monkeypatch):
    calls = []

    async def mock_post(self, path: str, body: dict[str, Any]):
        calls.append((path, body))
        return {
            "uuid": "test-uuid-1234",
            "reach": [50000, 150000],
            "result": [1200, 3500],
            "absentFields": [],
            "invalidFields": [],
            "ignoredFields": [],
        }

    monkeypatch.setattr(LineAdsClient, "post", mock_post)

    res = await estimate_adset_reach(
        campaign_id="camp-123",
        campaign_objective="GAIN_FRIENDS",
        daily_budget=250.5,
        bid_type="CPF",
        auto_bid_type="FRIEND",
        adset_id="adset-456",
        bid_amount=15.0,
        bid_strategy="COST_CAP",
        age_min=25,
        age_max=44,
    )

    assert res["ok"] is True
    data = res["data"]
    assert data["reach"] == {"min": 50000, "max": 150000}
    assert data["clicks"] == {"min": 1200, "max": 3500}
    assert data["absent_fields"] == []
    assert data["invalid_fields"] == []
    assert data["ignored_fields"] == []
    assert data["note"] == NOTE_ARS

    assert len(calls) == 1
    path, body = calls[0]
    assert path == "/adaccounts/A01887296807/simulation/ars"
    assert body["adaccountId"] == "A01887296807"
    assert body["campaignId"] == "camp-123"
    assert body["adgroupId"] == "adset-456"
    assert body["campaignObjective"] == "GAIN_FRIENDS"
    assert body["dailyBudgetMicro"] == 250_500_000
    assert body["bidAmountMicro"] == 15_000_000
    assert body["bidType"] == "CPF"
    assert body["bidStrategy"] == "COST_CAP"
    assert body["autoBidType"] == "FRIEND"
    assert "dailyBudget" not in body
    assert "bidAmount" not in body
    assert data["request"] == body


@pytest.mark.asyncio
async def test_targeting_identical_to_create_adset_dry_run(monkeypatch):
    """Targeting must be byte-identical to what create_adset produces for same inputs."""
    calls = []

    async def mock_post(self, path: str, body: dict[str, Any]):
        calls.append((path, body))
        return {
            "uuid": "test-uuid-ars",
            "reach": [10000, 20000],
            "result": [100, 200],
        }

    monkeypatch.setattr(LineAdsClient, "post", mock_post)

    params = {
        "age_min": 25,
        "age_max": 54,
        "country": "TH",
        "genders": ["FEMALE"],
        "interest_codes": ["4", "12"],
        "excluded_audience_ids": ["aud-ex-1"],
        "custom_audience_ids": ["aud-in-1"],
    }

    # 1. Call estimate_adset_reach
    res_sim = await estimate_adset_reach(
        campaign_id="camp-123",
        campaign_objective="GAIN_FRIENDS",
        daily_budget=100,
        bid_strategy="LOWEST_COST",
        bid_type="CPF",
        auto_bid_type="FRIEND",
        **params,
    )
    assert res_sim["ok"] is True
    sim_targeting = calls[0][1]["targeting"]

    # 2. Call create_adset dry run
    # Note: create_adset uses excluded_audience_ids parameter name
    res_adset = await create_adset(
        campaign_id="camp-123",
        name="Targeting Test Adset",
        bid_type="CPF",
        bid_strategy="COST_CAP",
        bid_amount=20,
        auto_bid_type="FRIEND",
        daily_budget=100,
        age_min=params["age_min"],
        age_max=params["age_max"],
        country=params["country"],
        genders=params["genders"],
        interest_codes=params["interest_codes"],
        excluded_audience_ids=params["excluded_audience_ids"],
        custom_audience_ids=params["custom_audience_ids"],
        dry_run=True,
    )
    assert res_adset["ok"] is True
    adset_targeting = res_adset["payload"]["targeting"]

    assert sim_targeting == adset_targeting


@pytest.mark.asyncio
async def test_raw_targeting_adjusted_without_mutating_caller(monkeypatch):
    calls = []

    async def mock_post(self, path: str, body: dict[str, Any]):
        calls.append((path, body))
        return {
            "uuid": "uuid",
            "reach": [10, 20],
            "result": [1, 2],
        }

    monkeypatch.setattr(LineAdsClient, "post", mock_post)

    raw_targeting = {
        "targetingMode": "CUSTOM",
        "someCustomKey": "customValue",
        "country": "TH",
    }

    res = await estimate_adset_reach(
        campaign_id="camp-1",
        campaign_objective="CONVERSIONS",
        daily_budget=100,
        bid_strategy="LOWEST_COST",
        bid_type="CPC",
        auto_bid_type="CLICK",
        targeting=raw_targeting,
    )
    assert res["ok"] is True
    assert raw_targeting["targetingMode"] == "CUSTOM"
    assert calls[0][1]["targeting"] == {**raw_targeting, "targetingMode": "MANUAL"}
    assert res["data"]["adjusted"] == ["targetingMode AUTO→MANUAL (ARS รับเฉพาะ MANUAL)"]


@pytest.mark.asyncio
async def test_invalid_enum_rejected_before_any_request(monkeypatch):
    calls = []

    async def mock_post(self, path: str, body: dict[str, Any]):
        calls.append((path, body))
        return {}

    monkeypatch.setattr(LineAdsClient, "post", mock_post)

    # Invalid campaign_objective
    res = await estimate_adset_reach(
        campaign_id="camp-1",
        campaign_objective="INVALID_OBJ",
        daily_budget=100,
        bid_strategy="LOWEST_COST",
        bid_type="CPC",
        auto_bid_type="CLICK",
    )
    assert res["ok"] is False
    assert "campaign_objective" in res["message"]
    assert len(calls) == 0

    # Invalid bid_type (CPV is in BID_TYPES for adsets, but ARS only accepts CPC, CPF, CPM)
    res2 = await estimate_adset_reach(
        campaign_id="camp-1",
        campaign_objective="GAIN_FRIENDS",
        daily_budget=100,
        bid_strategy="LOWEST_COST",
        bid_type="CPV",
        auto_bid_type="FRIEND",
    )
    assert res2["ok"] is False
    assert "bid_type" in res2["message"]
    assert len(calls) == 0

    # Invalid auto_bid_type
    res3 = await estimate_adset_reach(
        campaign_id="camp-1",
        campaign_objective="GAIN_FRIENDS",
        daily_budget=100,
        bid_strategy="LOWEST_COST",
        bid_type="CPF",
        auto_bid_type="INVALID_AUTO_BID",
    )
    assert res3["ok"] is False
    assert "auto_bid_type" in res3["message"]
    assert len(calls) == 0

    # Invalid bid_strategy
    res4 = await estimate_adset_reach(
        campaign_id="camp-1",
        campaign_objective="GAIN_FRIENDS",
        daily_budget=100,
        bid_type="CPF",
        auto_bid_type="FRIEND",
        bid_strategy="INVALID_STRATEGY",
    )
    assert res4["ok"] is False
    assert "bid_strategy" in res4["message"]
    assert len(calls) == 0


@pytest.mark.asyncio
async def test_missing_reach_handled(monkeypatch):
    """If reach missing → ok with reach None and the API's absent/invalid fields so Claude can ask user."""
    async def mock_post(self, path: str, body: dict[str, Any]):
        return {
            "uuid": "test-uuid-ars",
            "absentFields": ["targeting.locations"],
            "invalidFields": ["dailyBudgetMicro"],
            "ignoredFields": [],
        }

    monkeypatch.setattr(LineAdsClient, "post", mock_post)

    res = await estimate_adset_reach(
        campaign_id="camp-123",
        campaign_objective="GAIN_FRIENDS",
        daily_budget=100,
        bid_strategy="LOWEST_COST",
        bid_type="CPF",
        auto_bid_type="FRIEND",
    )
    assert res["ok"] is True
    data = res["data"]
    assert data["reach"] is None
    assert data["clicks"] is None
    assert data["absent_fields"] == ["targeting.locations"]
    assert data["invalid_fields"] == ["dailyBudgetMicro"]
    assert data["ignored_fields"] == []
    assert data["note"] == NOTE_ARS


@pytest.mark.asyncio
async def test_api_error_passthrough(monkeypatch):
    async def mock_post(self, path: str, body: dict[str, Any]):
        raise LineAdsAPIError(400, "Daily budget must be higher", "BUDGET_TOO_LOW")

    monkeypatch.setattr(LineAdsClient, "post", mock_post)

    res = await estimate_adset_reach(
        campaign_id="camp-123",
        campaign_objective="GAIN_FRIENDS",
        daily_budget=10,
        bid_strategy="LOWEST_COST",
        bid_type="CPF",
        auto_bid_type="FRIEND",
    )
    assert res["ok"] is False
    assert res["status_code"] == 400
    assert res["error_code"] == "BUDGET_TOO_LOW"
    assert "Daily budget must be higher" in res["message"]


@pytest.mark.parametrize("targeting", [None, {"targetingMode": "AUTO", "country": "TH"},
                                      {"country": "TH"}, {"targetingMode": "MANUAL"}])
async def test_ars_always_uses_manual(monkeypatch, targeting):
    calls = []

    async def post(self, path, body):
        calls.append(body)
        return {"reach": [1, 2]}

    monkeypatch.setattr(LineAdsClient, "post", post)
    original = dict(targeting) if targeting is not None else None
    result = await estimate_adset_reach("c1", "REACH", 100, "CPM", "REACH",
                                        bid_strategy="LOWEST_COST", targeting=targeting)
    assert result["ok"] is True
    assert calls[0]["targeting"]["targetingMode"] == "MANUAL"
    assert "bidAmountMicro" not in calls[0]
    assert targeting == original
    adjusted = targeting is not None and targeting.get("targetingMode") != "MANUAL"
    assert ("adjusted" in result["data"]) is adjusted


@pytest.mark.parametrize("bid_strategy,bid_amount,valid", [
    (None, None, False), ("COST_CAP", None, False), ("LOWEST_COST", None, True),
    (None, 5, True), ("COST_CAP", 5, True),
])
async def test_ars_bid_requirement_before_http(monkeypatch, bid_strategy, bid_amount, valid):
    calls = []

    async def post(self, path, body):
        calls.append(body)
        return {}

    monkeypatch.setattr(LineAdsClient, "post", post)
    result = await estimate_adset_reach("c1", "GAIN_FRIENDS", 100, "CPF", "FRIEND",
                                        bid_strategy=bid_strategy, bid_amount=bid_amount)
    assert result["ok"] is valid
    assert len(calls) == int(valid)
    if not valid:
        assert result["status_code"] == 400
        assert result["error_code"] == "VALIDATION_ERROR"
        assert result["message"] == 'ต้องระบุ bid_amount เมื่อ bid_strategy เป็น COST_CAP หรือไม่ระบุ หรือใช้ bid_strategy="LOWEST_COST"'
