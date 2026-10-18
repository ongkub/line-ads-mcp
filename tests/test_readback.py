"""Write safety contracts: no dry-run I/O, before snapshots and readback."""

import pytest

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient, LineAdsConfig
from line_ads_mcp.tools.ads import create_ad, pause_ad, resume_ad
from line_ads_mcp.tools.adsets import create_adset, pause_adset, resume_adset, update_adset
from line_ads_mcp.tools.campaigns import create_campaign, pause_campaign, resume_campaign, update_campaign

CREATES = [
    (create_campaign, dict(name="ทดสอบ", objective="GAIN_FRIENDS", start_date="2026-10-19T09:00:00+07:00"), "campaigns"),
    (create_adset, dict(campaign_id="c1", name="ทดสอบ", bid_type="CPF", bid_strategy="LOWEST_COST", auto_bid_type="FRIEND", daily_budget=100), "adgroups"),
    (create_ad, dict(adset_id="s1", name="ทดสอบ", image_hash="hash", title="ทดสอบ", call_to_action="ADD_FRIEND"), "ads"),
]
UPDATES = [
    (update_campaign, "campaigns", {"status": "ACTIVE"}),
    (update_adset, "adgroups", {"status": "ACTIVE"}),
    (pause_campaign, "campaigns", {}), (resume_campaign, "campaigns", {}),
    (pause_adset, "adgroups", {}), (resume_adset, "adgroups", {}),
    (pause_ad, "ads", {}), (resume_ad, "ads", {}),
]


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A123")
    monkeypatch.delenv("LINE_ADS_WORKSPACE_DIR", raising=False)


def no_client(*args, **kwargs):
    pytest.fail("dry run / invalid status must not construct a client")


@pytest.mark.parametrize("tool,arguments,collection", CREATES)
@pytest.mark.parametrize("status", [None, "ACTIVE"])
async def test_create_status_dry_run(monkeypatch, tool, arguments, collection, status):
    monkeypatch.setattr(LineAdsClient, "__init__", no_client)
    result = await tool(**arguments, **({"status": status} if status else {}))
    assert result["dry_run"] is True
    assert result["payload"]["configuredStatus"] == (status or "PAUSED")
    assert result["endpoint"] == f"/adaccounts/A123/{collection}"


@pytest.mark.parametrize("tool,arguments,collection", CREATES)
@pytest.mark.parametrize("status", ["DRAFT", "junk", "", None])
async def test_create_status_validated_first(monkeypatch, tool, arguments, collection, status):
    monkeypatch.setattr(LineAdsClient, "__init__", no_client)
    monkeypatch.setattr(LineAdsConfig, "from_env", no_client)
    result = await tool(**arguments, status=status, dry_run=False)
    assert result["ok"] is False
    assert result["error_code"] == "VALIDATION_ERROR"
    assert "status" in result["message"]


@pytest.mark.parametrize("tool,arguments,collection", CREATES)
@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("status", ["PAUSED", "ACTIVE"])
async def test_real_create_reads_back_on_same_client(monkeypatch, tool, arguments, collection, nested, status):
    calls = []

    async def post(self, path, body):
        calls.append(("POST", self, path, body))
        return {"datas": [{"id": "new1"}]} if nested else {"id": "new1"}

    async def get(self, path, params=None):
        calls.append(("GET", self, path, params))
        return {"datas": [{"id": "new1", "configuredStatus": status, "deliveryStatus": "NOT_DELIVERING", "dailyBudgetMicro": 100_000_000, "bidAmountMicro": 3_000_000}]}

    monkeypatch.setattr(LineAdsClient, "post", post)
    monkeypatch.setattr(LineAdsClient, "get", get)
    result = await tool(**arguments, status=status, dry_run=False)
    assert result["ok"] is True
    assert result["readback_ok"] is True
    assert result["readback_mismatch"] == []
    assert result["readback"]["configured_status"] == status
    assert result["readback"]["delivery_status"] == "NOT_DELIVERING"
    assert result["readback"]["dailyBudgetMicro"] == 100_000_000
    assert result["readback"]["bidAmountMicro"] == 3_000_000
    assert [c[0] for c in calls] == ["POST", "GET"]
    assert calls[0][1] is calls[1][1]
    assert calls[0][2] == calls[1][2] == f"/adaccounts/A123/{collection}"
    assert calls[1][3] == {"ids": "new1", "includeRemoved": "true"}


@pytest.mark.parametrize("tool,arguments,collection", CREATES)
@pytest.mark.parametrize("failure", ["mismatch", "raises", "missing", "no_id"])
async def test_create_readback_failure_preserves_write(monkeypatch, tool, arguments, collection, failure):
    async def post(self, path, body):
        return {} if failure == "no_id" else {"id": "new1"}

    async def get(self, path, params=None):
        if failure == "raises":
            raise RuntimeError("readback failed")
        return {"datas": [] if failure == "missing" else [{"id": "new1", "configuredStatus": "ACTIVE"}]}

    monkeypatch.setattr(LineAdsClient, "post", post)
    monkeypatch.setattr(LineAdsClient, "get", get)
    result = await tool(**arguments, dry_run=False)
    assert result["ok"] is True
    assert result["data"] == ({} if failure == "no_id" else {"id": "new1"})
    if failure == "mismatch":
        assert result["readback_ok"] is False
        assert result["readback_mismatch"] == ["configuredStatus"]
    else:
        assert result["readback_ok"] is None
        assert result["readback_error"]


@pytest.mark.parametrize("tool,collection,arguments", UPDATES)
async def test_updates_fetch_before_post_after(monkeypatch, tool, collection, arguments):
    calls = []
    status = "PAUSED" if tool.__name__.startswith("pause_") else "ACTIVE"
    before = {"id": "e1", "configuredStatus": "PAUSED", "name": "เดิม", "deliveryStatus": "PAUSED", "modifiedDate": "2026-10-01"}

    async def get(self, path, params=None):
        calls.append(("GET", self, path, params))
        return {"datas": [before if len(calls) == 1 else {"id": "e1", "configuredStatus": status}]}

    async def post(self, path, body):
        calls.append(("POST", self, path, body))
        return {}

    monkeypatch.setattr(LineAdsClient, "get", get)
    monkeypatch.setattr(LineAdsClient, "post", post)
    result = await tool("e1", **arguments, dry_run=False)
    assert result["ok"] is True
    assert result["before"] == before
    assert result["readback_ok"] is True
    assert [c[0] for c in calls] == ["GET", "POST", "GET"]
    assert calls[0][1] is calls[1][1] is calls[2][1]
    assert calls[1][2] == f"/adaccounts/A123/{collection}/e1"
    # Full entity body: current values minus read-only fields, then the requested change.
    assert calls[1][3] == {"id": "e1", "name": "เดิม", "configuredStatus": status}


@pytest.mark.parametrize("tool,collection,arguments", UPDATES)
async def test_missing_update_entity_never_posts(monkeypatch, tool, collection, arguments):
    async def get(self, path, params=None):
        return {"datas": []}

    monkeypatch.setattr(LineAdsClient, "get", get)
    monkeypatch.setattr(LineAdsClient, "post", no_client)
    result = await tool("missing", **arguments, dry_run=False)
    assert result["ok"] is False
    assert result["error_code"] == "NOT_FOUND"


@pytest.mark.parametrize("tool,collection,arguments", UPDATES)
async def test_update_before_failure_never_posts(monkeypatch, tool, collection, arguments):
    async def get(self, path, params=None):
        raise LineAdsAPIError(403, "no read access", "FORBIDDEN")

    monkeypatch.setattr(LineAdsClient, "get", get)
    monkeypatch.setattr(LineAdsClient, "post", no_client)
    result = await tool("e1", **arguments, dry_run=False)
    assert result["error_code"] == "FORBIDDEN"


@pytest.mark.parametrize("tool,arguments", [(update_campaign, dict(daily_budget=250)), (update_adset, dict(daily_budget=250, bid_amount=7))])
@pytest.mark.parametrize("failure", ["none", "budget", "missing_bid", "raises"])
async def test_update_money_readback(monkeypatch, tool, arguments, failure):
    before = {"id": "e1", "configuredStatus": "ACTIVE", "dailyBudgetMicro": 100_000_000, "bidAmountMicro": 2_000_000}
    after = dict(before, dailyBudgetMicro=250_000_000, bidAmountMicro=7_000_000)
    if failure == "budget":
        after["dailyBudgetMicro"] = before["dailyBudgetMicro"]
    if failure == "missing_bid":
        after.pop("bidAmountMicro")
    reads = 0

    async def get(self, path, params=None):
        nonlocal reads
        reads += 1
        if reads == 2 and failure == "raises":
            raise RuntimeError("readback unavailable")
        return {"datas": [before if reads == 1 else after]}

    async def post(self, path, body):
        assert body["dailyBudgetMicro"] == 250_000_000
        return {"saved": True}

    monkeypatch.setattr(LineAdsClient, "get", get)
    monkeypatch.setattr(LineAdsClient, "post", post)
    result = await tool("e1", **arguments, dry_run=False)
    assert result["ok"] is True
    assert result["before"] == before
    if failure == "raises":
        assert result["readback_ok"] is None
        assert "unavailable" in result["readback_error"]
    else:
        expected = ["dailyBudgetMicro"] if failure == "budget" else (["bidAmountMicro"] if failure == "missing_bid" and tool is update_adset else [])
        assert result["readback_mismatch"] == expected
        assert result["readback_ok"] is (not expected)


@pytest.mark.parametrize("tool,status", [(pause_ad, "PAUSED"), (resume_ad, "ACTIVE")])
async def test_ad_status_dry_run(monkeypatch, tool, status):
    monkeypatch.setattr(LineAdsClient, "__init__", no_client)
    result = await tool("ad1")
    assert result["dry_run"] is True
    assert result["payload"] == {"configuredStatus": status}
    assert result["endpoint"] == "/adaccounts/A123/ads/ad1"


@pytest.mark.parametrize("tool,collection,arguments", UPDATES)
@pytest.mark.parametrize("failure", ["mismatch", "raises"])
async def test_status_update_readback_failure_keeps_write_success(monkeypatch, tool, collection, arguments, failure):
    reads = 0
    sent_status = "PAUSED" if tool.__name__.startswith("pause_") else "ACTIVE"

    async def get(self, path, params=None):
        nonlocal reads
        reads += 1
        if reads == 2 and failure == "raises":
            raise RuntimeError("readback failed")
        return {"datas": [{"id": "e1", "configuredStatus": "ACTIVE" if sent_status == "PAUSED" else "PAUSED"}]}

    async def post(self, path, body):
        return {"saved": True}

    monkeypatch.setattr(LineAdsClient, "get", get)
    monkeypatch.setattr(LineAdsClient, "post", post)
    result = await tool("e1", **arguments, dry_run=False)
    assert result["ok"] is True
    assert result["data"] == {"saved": True}
    if failure == "raises":
        assert result["readback_ok"] is None
        assert result["readback_error"] == "readback failed"
    else:
        assert result["readback_ok"] is False
        assert result["readback_mismatch"] == ["configuredStatus"]


async def test_pause_ad_sends_full_ad_body(monkeypatch):
    """Ad update requires adgroupId/name/creative per v3.12.3 docs; untouched fields must be preserved."""
    before = {
        "id": "ad1",
        "adgroupId": 77,
        "name": "โฆษณาเดิม",
        "configuredStatus": "ACTIVE",
        "creative": {"title": "หัวข้อ", "mediaIds": [5]},
        "deliveryStatus": "ACTIVE",
        "deliveryStatusReasons": [],
        "createdDate": "2026-10-01T00:00:00Z",
    }
    sent = {}

    async def get(self, path, params=None):
        return {"datas": [before if not sent else dict(before, configuredStatus="PAUSED")]}

    async def post(self, path, body):
        sent.update(body)
        return {"id": "ad1"}

    monkeypatch.setattr(LineAdsClient, "get", get)
    monkeypatch.setattr(LineAdsClient, "post", post)
    result = await pause_ad("ad1", dry_run=False)
    assert result["ok"] is True and result["readback_ok"] is True
    assert sent == {
        "id": "ad1",
        "adgroupId": 77,
        "name": "โฆษณาเดิม",
        "configuredStatus": "PAUSED",
        "creative": {"title": "หัวข้อ", "mediaIds": [5]},
    }


def test_merge_update_body_keeps_unmentioned_targeting_keys():
    from line_ads_mcp.tools.change_log import merge_update_body

    before = {"id": 1, "name": "เดิม", "deliveryStatus": "ACTIVE",
              "targeting": {"age": {"min": 20}, "advancedTargeting": {"groups": [1]}}}
    body = merge_update_body(before, {"targeting": {"age": {"min": 25, "max": 34}}})
    assert body == {"id": 1, "name": "เดิม",
                    "targeting": {"age": {"min": 25, "max": 34}, "advancedTargeting": {"groups": [1]}}}
