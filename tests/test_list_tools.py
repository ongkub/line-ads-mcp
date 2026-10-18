"""Tests for fetch-all list tools with status filtering and pagination."""

from typing import Any
import pytest

from line_ads_mcp.client import LineAdsClient
from line_ads_mcp.tools.ads import list_ads
from line_ads_mcp.tools.adsets import list_adsets
from line_ads_mcp.tools.campaigns import list_campaigns


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A01887296807")


# ---------------------------------------------------------------------------
# list_campaigns tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_campaigns_paging_across_2_pages(monkeypatch):
    calls: list[dict[str, Any]] = []

    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        calls.append({"path": path, "params": dict(params or {})})
        page = (params or {}).get("page", 1)
        if page == 1:
            return {
                "paging": {"page": 1, "size": 2, "totalElements": 3},
                "datas": [
                    {"id": "camp_1", "name": "Campaign 1", "configuredStatus": "ACTIVE"},
                    {"id": "camp_2", "name": "Campaign 2", "configuredStatus": "PAUSED"},
                ],
            }
        return {
            "paging": {"page": 2, "size": 2, "totalElements": 3},
            "datas": [
                {"id": "camp_3", "name": "Campaign 3", "configuredStatus": "ACTIVE"},
            ],
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await list_campaigns(fetch_all=True, size=2)

    assert result["ok"] is True
    data = result["data"]
    assert len(data["datas"]) == 3
    assert [row["id"] for row in data["datas"]] == ["camp_1", "camp_2", "camp_3"]
    assert data["paging"]["complete"] is True
    assert data["paging"]["pages_fetched"] == 2
    assert data["paging"]["total_elements"] == 3
    assert data["status_filter"] is None
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_list_campaigns_status_filter_active(monkeypatch):
    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        return {
            "paging": {"page": 1, "size": 100, "totalElements": 3},
            "datas": [
                {"id": "camp_1", "configuredStatus": "ACTIVE"},
                {"id": "camp_2", "configuredStatus": "PAUSED"},
                {"id": "camp_3", "configuredStatus": "ACTIVE"},
            ],
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await list_campaigns(status="ACTIVE", fetch_all=True)

    assert result["ok"] is True
    datas = result["data"]["datas"]
    assert len(datas) == 2
    assert all(row["configuredStatus"] == "ACTIVE" for row in datas)
    assert result["data"]["status_filter"] == "ACTIVE"


@pytest.mark.asyncio
async def test_list_campaigns_removed_adds_include_removed(monkeypatch):
    recorded_params = {}

    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        nonlocal recorded_params
        recorded_params = dict(params or {})
        return {
            "paging": {"page": 1, "size": 100, "totalElements": 1},
            "datas": [{"id": "camp_rem", "configuredStatus": "REMOVED"}],
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await list_campaigns(status="REMOVED")

    assert result["ok"] is True
    assert recorded_params.get("includeRemoved") == "true"
    assert len(result["data"]["datas"]) == 1
    assert result["data"]["datas"][0]["configuredStatus"] == "REMOVED"


@pytest.mark.asyncio
async def test_list_campaigns_active_omits_include_removed(monkeypatch):
    recorded_params = {}

    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        nonlocal recorded_params
        recorded_params = dict(params or {})
        return {
            "paging": {"page": 1, "size": 100, "totalElements": 0},
            "datas": [],
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    await list_campaigns(status="ACTIVE")
    assert "includeRemoved" not in recorded_params


@pytest.mark.asyncio
async def test_list_campaigns_single_page(monkeypatch):
    recorded_params = {}

    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        nonlocal recorded_params
        recorded_params = dict(params or {})
        return {
            "paging": {"page": 2, "size": 25, "totalElements": 100},
            "datas": [{"id": "c1", "configuredStatus": "ACTIVE"}],
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await list_campaigns(fetch_all=False, page=2, size=25)

    assert result["ok"] is True
    assert recorded_params["page"] == 2
    assert recorded_params["size"] == 25
    assert result["data"]["paging"]["page"] == 2


@pytest.mark.asyncio
async def test_list_campaigns_invalid_status():
    result = await list_campaigns(status="INVALID")
    assert result["ok"] is False
    assert result["error_code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# list_adsets tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_adsets_without_campaign_id_omits_campaign_id(monkeypatch):
    recorded_params = {}

    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        nonlocal recorded_params
        recorded_params = dict(params or {})
        return {
            "paging": {"page": 1, "size": 100, "totalElements": 1},
            "datas": [{"id": "adset_1", "configuredStatus": "ACTIVE"}],
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await list_adsets()

    assert result["ok"] is True
    assert "campaignId" not in recorded_params
    assert recorded_params.get("includeRemoved") is None


@pytest.mark.asyncio
async def test_list_adsets_with_campaign_id(monkeypatch):
    recorded_params = {}

    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        nonlocal recorded_params
        recorded_params = dict(params or {})
        return {
            "paging": {"page": 1, "size": 100, "totalElements": 1},
            "datas": [{"id": "adset_1", "configuredStatus": "ACTIVE"}],
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await list_adsets(campaign_id="camp_999")

    assert result["ok"] is True
    assert recorded_params.get("campaignId") == "camp_999"


@pytest.mark.asyncio
async def test_list_adsets_status_filter_and_paging(monkeypatch):
    calls: list[dict[str, Any]] = []

    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        calls.append({"path": path, "params": dict(params or {})})
        page = (params or {}).get("page", 1)
        if page == 1:
            return {
                "paging": {"page": 1, "size": 2, "totalElements": 3},
                "datas": [
                    {"id": "ag_1", "configuredStatus": "ACTIVE"},
                    {"id": "ag_2", "configuredStatus": "PAUSED"},
                ],
            }
        return {
            "paging": {"page": 2, "size": 2, "totalElements": 3},
            "datas": [
                {"id": "ag_3", "configuredStatus": "ACTIVE"},
            ],
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await list_adsets(status="ACTIVE", fetch_all=True, size=2)

    assert result["ok"] is True
    assert len(result["data"]["datas"]) == 2
    assert [r["id"] for r in result["data"]["datas"]] == ["ag_1", "ag_3"]
    assert result["data"]["status_filter"] == "ACTIVE"


@pytest.mark.asyncio
async def test_list_adsets_removed_adds_include_removed(monkeypatch):
    recorded_params = {}

    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        nonlocal recorded_params
        recorded_params = dict(params or {})
        return {
            "paging": {"page": 1, "size": 100, "totalElements": 0},
            "datas": [],
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    await list_adsets(status="REMOVED")
    assert recorded_params.get("includeRemoved") == "true"


# ---------------------------------------------------------------------------
# list_ads tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_ads_with_campaign_id(monkeypatch):
    recorded_params = {}

    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        nonlocal recorded_params
        recorded_params = dict(params or {})
        return {
            "paging": {"page": 1, "size": 100, "totalElements": 1},
            "datas": [{"id": "ad_1", "configuredStatus": "ACTIVE"}],
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await list_ads(campaign_id="camp_100")

    assert result["ok"] is True
    assert recorded_params.get("campaignId") == "camp_100"
    assert "adgroupId" not in recorded_params


@pytest.mark.asyncio
async def test_list_ads_with_adset_id(monkeypatch):
    recorded_params = {}

    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        nonlocal recorded_params
        recorded_params = dict(params or {})
        return {
            "paging": {"page": 1, "size": 100, "totalElements": 1},
            "datas": [{"id": "ad_1", "configuredStatus": "ACTIVE"}],
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await list_ads(adset_id="ag_200")

    assert result["ok"] is True
    assert recorded_params.get("adgroupId") == "ag_200"
    assert "campaignId" not in recorded_params


@pytest.mark.asyncio
async def test_list_ads_without_filters(monkeypatch):
    recorded_params = {}

    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        nonlocal recorded_params
        recorded_params = dict(params or {})
        return {
            "paging": {"page": 1, "size": 100, "totalElements": 0},
            "datas": [],
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await list_ads()

    assert result["ok"] is True
    assert "adgroupId" not in recorded_params
    assert "campaignId" not in recorded_params


@pytest.mark.asyncio
async def test_list_ads_status_filter_and_removed(monkeypatch):
    recorded_params = {}

    async def mock_get(self, path: str, params: dict[str, Any] | None = None):
        nonlocal recorded_params
        recorded_params = dict(params or {})
        return {
            "paging": {"page": 1, "size": 100, "totalElements": 2},
            "datas": [
                {"id": "ad_1", "configuredStatus": "REMOVED"},
                {"id": "ad_2", "configuredStatus": "ACTIVE"},
            ],
        }

    monkeypatch.setattr(LineAdsClient, "get", mock_get)

    result = await list_ads(status="REMOVED")

    assert result["ok"] is True
    assert recorded_params.get("includeRemoved") == "true"
    assert len(result["data"]["datas"]) == 1
    assert result["data"]["datas"][0]["id"] == "ad_1"
