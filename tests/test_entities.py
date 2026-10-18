"""Tests for entity lookup and inspection (get_entity, fetch_entity, get_ad_status)."""

from typing import Any
import pytest

from line_ads_mcp.client import LineAdsClient, LineAdsConfig
from line_ads_mcp.tools.ads import get_ad_status
from line_ads_mcp.tools.entities import fetch_entity, get_entity


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A01887296807")


@pytest.mark.asyncio
async def test_get_entity_exact_match_among_several_rows(monkeypatch):
    recorded = {}

    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        recorded["path"] = path
        recorded["params"] = dict(params or {})
        return {
            "datas": [
                {"id": "111", "name": "Ad 1", "configuredStatus": "PAUSED"},
                {"id": "222", "name": "Ad 2", "configuredStatus": "ACTIVE", "deliveryStatus": "ACTIVE"},
                {"id": "333", "name": "Ad 3", "configuredStatus": "REMOVED"},
            ]
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await get_entity("ad", "222")

    assert result["ok"] is True
    data = result["data"]
    assert data["entity_type"] == "ad"
    assert data["id"] == "222"
    assert data["name"] == "Ad 2"
    assert data["configured_status"] == "ACTIVE"
    assert data["delivery_status"] == "ACTIVE"
    assert data["raw"]["id"] == "222"
    assert "fetched_at" in data
    assert recorded["path"] == "/adaccounts/A01887296807/ads"
    assert recorded["params"]["ids"] == "222"
    assert recorded["params"]["includeRemoved"] == "true"


@pytest.mark.asyncio
async def test_get_entity_wrong_id_not_found(monkeypatch):
    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        return {
            "datas": [
                {"id": "111", "name": "Campaign 1"},
            ]
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await get_entity("campaign", "999")

    assert result["ok"] is False
    assert result["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_entity_empty_datas_not_found(monkeypatch):
    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        return {"datas": []}

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await get_entity("campaign", "111")

    assert result["ok"] is False
    assert result["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_entity_micro_to_thb_budget(monkeypatch):
    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        return {
            "datas": [
                {
                    "id": "camp_b1",
                    "name": "Budget Camp",
                    "configuredStatus": "ACTIVE",
                    "dailyBudgetMicro": 300_000_000,
                    "totalBudgetMicro": 9_000_000_000,
                }
            ]
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await get_entity("campaign", "camp_b1")

    assert result["ok"] is True
    budget = result["data"]["budget"]
    # 300,000,000 micro = 300.0 THB
    assert budget["daily_budget_thb"] == 300.0
    # 9,000,000,000 micro = 9,000.0 THB
    assert budget["total_budget_thb"] == 9000.0


@pytest.mark.asyncio
async def test_get_entity_bid_and_targeting(monkeypatch):
    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        return {
            "datas": [
                {
                    "id": "ag_1",
                    "name": "Targeting Group",
                    "configuredStatus": "ACTIVE",
                    "bidType": "CPF",
                    "bidStrategy": "COST_CAP",
                    "autoBidType": "FRIEND",
                    "bidAmountMicro": 25_000_000,
                    "targeting": {
                        "targetingMode": "AUTO",
                        "ageMin": 20,
                        "country": "TH",
                    },
                }
            ]
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await get_entity("adset", "ag_1")

    assert result["ok"] is True
    bid = result["data"]["bid"]
    assert bid["bidType"] == "CPF"
    assert bid["bidStrategy"] == "COST_CAP"
    assert bid["autoBidType"] == "FRIEND"
    assert bid["bid_amount_thb"] == 25.0

    targeting = result["data"]["targeting"]
    assert targeting["targetingMode"] == "AUTO"
    assert targeting["ageMin"] == 20
    assert targeting["country"] == "TH"


@pytest.mark.asyncio
async def test_get_entity_review_extraction(monkeypatch):
    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        return {
            "datas": [
                {
                    "id": "ad_rev",
                    "name": "Review Ad",
                    "configuredStatus": "ACTIVE",
                    "review": {"status": "APPROVED", "reason": None},
                }
            ]
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await get_entity("ad", "ad_rev")

    assert result["ok"] is True
    assert result["data"]["review"] == {"status": "APPROVED", "reason": None}


@pytest.mark.asyncio
async def test_get_entity_invalid_entity_type():
    result = await get_entity("unknown_type", "123")

    assert result["ok"] is False
    assert result["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_fetch_entity_helper(monkeypatch):
    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        return {
            "datas": [
                {"id": "c100", "name": "Direct Campaign"},
            ]
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    config = LineAdsConfig.from_env()
    async with LineAdsClient(config) as client:
        row = await fetch_entity(client, "A01887296807", "campaign", "c100")
        assert row is not None
        assert row["id"] == "c100"

        missing = await fetch_entity(client, "A01887296807", "campaign", "c999")
        assert missing is None


# ---------------------------------------------------------------------------
# get_ad_status tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_ad_status_returns_raw_plus_status_keys(monkeypatch):
    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        return {
            "datas": [
                {
                    "id": "ad_456",
                    "name": "Ad 456",
                    "configuredStatus": "ACTIVE",
                    "deliveryStatus": "NOT_DELIVERING",
                    "creative": {"title": "Hello", "creativeFormat": "IMAGE"},
                }
            ]
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await get_ad_status("ad_456")

    assert result["ok"] is True
    ad_data = result["data"]
    # Raw ad row fields are present
    assert ad_data["id"] == "ad_456"
    assert ad_data["name"] == "Ad 456"
    assert ad_data["creative"] == {"title": "Hello", "creativeFormat": "IMAGE"}
    # Plus configured_status / delivery_status keys
    assert ad_data["configured_status"] == "ACTIVE"
    assert ad_data["delivery_status"] == "NOT_DELIVERING"


@pytest.mark.asyncio
async def test_get_ad_status_mismatch_protection(monkeypatch):
    """Ensure get_ad_status never returns a row whose id != ad_id."""
    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        # API returned a completely different row
        return {
            "datas": [
                {
                    "id": "different_ad_id",
                    "name": "Wrong Ad",
                    "configuredStatus": "ACTIVE",
                    "deliveryStatus": "ACTIVE",
                }
            ]
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await get_ad_status("requested_ad_id")

    assert result["ok"] is False
    assert result["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_ad_status_empty_datas(monkeypatch):
    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        return {"datas": []}

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await get_ad_status("missing_ad_id")

    assert result["ok"] is False
    assert result["error_code"] == "NOT_FOUND"
