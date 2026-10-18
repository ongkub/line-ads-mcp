"""Audience contracts from LINE Ads v3.12.3; all HTTP calls are mocked."""

from copy import deepcopy
import json

import httpx
import pytest

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient
from line_ads_mcp.tools.audiences import AUDIENCE_FUNCTION_TYPES, create_audience, list_audiences


EXAMPLES = {
    "LOOKALIKE": ("lookalike", {"source": {"audienceGroupId": 123}, "volumeRate": {"auto": False, "rate": 0.05}}),
    "APP_EVENT": ("appEvent", {"actionType": "INSTALL", "retentionDays": 30, "matchMethod": "NONE"}),
    "WEBTRAFFIC": ("webtraffic", {"visitType": "VISIT_ALL", "retentionDays": 30}),
    "ACCOUNT_FRIENDS": ("accountFriends", {"friendStatus": "ACTIVE"}),
    "VIDEO_VIEW": ("videoView", {"eventType": "VIDEO_PLAY_3S", "mediaVideoId": 456, "recency": 30}),
    "IMAGE_CLICK": ("imageClick", {"eventType": "CLICK", "campaignId": 789, "recency": 30}),
}
ENDPOINT = "/adaccounts/A01887296807/custom-audiences"
ORIGINAL_REQUEST = LineAdsClient.request


@pytest.fixture(autouse=True)
def _env_and_no_network(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A01887296807")
    monkeypatch.delenv("LINE_ADS_WORKSPACE_DIR", raising=False)

    async def forbidden_request(*args, **kwargs):
        pytest.fail("Audience tests must never send HTTP requests")

    monkeypatch.setattr(LineAdsClient, "request", forbidden_request)


@pytest.fixture
def no_client(monkeypatch):
    def forbidden_client(*args, **kwargs):
        pytest.fail("Dry runs and invalid configs must not create a client")

    monkeypatch.setattr(LineAdsClient, "__init__", forbidden_client)


@pytest.mark.parametrize("function_type", EXAMPLES)
async def test_dry_run_payload_per_type_no_client_or_log(function_type, no_client, tmp_path, monkeypatch):
    key, config = deepcopy(EXAMPLES[function_type])
    original = deepcopy(config)
    monkeypatch.setenv("LINE_ADS_WORKSPACE_DIR", str(tmp_path))
    result = await create_audience("ทดสอบ", function_type, config, workspace_dir=str(tmp_path))
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["action"] == "create_audience"
    assert result["endpoint"] == ENDPOINT
    assert result["payload"] == {"name": "ทดสอบ", "functionType": function_type, key: config}
    assert config == original
    assert not (tmp_path / "line-ads-data").exists()
    assert "change_log" not in result


REQUIRED = {
    "LOOKALIKE": ["source", "volumeRate"],
    "APP_EVENT": ["actionType", "retentionDays", "matchMethod"],
    "WEBTRAFFIC": ["visitType", "retentionDays"],
    "ACCOUNT_FRIENDS": ["friendStatus"],
    "VIDEO_VIEW": ["eventType", "mediaVideoId", "recency"],
    "IMAGE_CLICK": ["eventType", "campaignId", "recency"],
}


@pytest.mark.parametrize("function_type,field", [(kind, field) for kind, fields in REQUIRED.items() for field in fields])
async def test_required_fields_before_request(function_type, field, no_client):
    config = deepcopy(EXAMPLES[function_type][1])
    del config[field]
    result = await create_audience("Test", function_type, config, dry_run=False)
    assert result["ok"] is False
    assert result["error_code"] == "VALIDATION_ERROR"
    assert f"config.{field}" in result["message"]


ENUMS = [
    ("WEBTRAFFIC", "visitType", "VISIT_ALL URL_MATCHING EVENT_MATCHING"),
    ("WEBTRAFFIC", "matchingType", "NONE NORMAL"),
    ("WEBTRAFFIC", "tagEventType", "CONVERSION_EVENT CUSTOM_EVENT"),
    ("APP_EVENT", "actionType", "INSTALL OPEN ADD_TO_CART PURCHASE VIEW_HOME VIEW_CATEGORY VIEW_ITEM SEARCH LEVEL_ACHIEVED TUTORIAL_COMPLETE CUSTOM"),
    ("APP_EVENT", "matchMethod", "NONE NORMAL"),
    ("ACCOUNT_FRIENDS", "friendStatus", "ACTIVE BLOCKED"),
    ("VIDEO_VIEW", "eventType", "CLICK PLAY_START VIDEO_PLAY_3S VIDEO_PLAY_25P VIDEO_PLAY_50P VIDEO_PLAY_75P VIDEO_PLAY_95P VIDEO_PLAY_COMPLETED"),
    ("IMAGE_CLICK", "eventType", "CLICK"),
]


@pytest.mark.parametrize("function_type,field,allowed", ENUMS)
async def test_enum_validation(function_type, field, allowed, no_client):
    config = deepcopy(EXAMPLES[function_type][1])
    for value in allowed.split():
        config[field] = value
        assert (await create_audience("Test", function_type, config))["ok"] is True
    for value in ("TYPO", [], None, 1):
        config[field] = value
        result = await create_audience("Test", function_type, config, dry_run=False)
        assert result["ok"] is False
        assert result["error_code"] == "VALIDATION_ERROR"
        assert field in result["message"]


@pytest.mark.parametrize("function_type", EXAMPLES)
async def test_unknown_fields_and_non_object_configs(function_type, no_client):
    config = deepcopy(EXAMPLES[function_type][1])
    config["typo"] = 1
    for bad in (config, None, [], "config", True):
        result = await create_audience("Test", function_type, bad, dry_run=False)
        assert result["ok"] is False
        assert result["error_code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("function_type,field", [
    ("WEBTRAFFIC", "retentionDays"), ("APP_EVENT", "retentionDays"),
    ("VIDEO_VIEW", "recency"), ("IMAGE_CLICK", "recency"),
])
async def test_retention_ranges(function_type, field, no_client):
    config = deepcopy(EXAMPLES[function_type][1])
    for value in (1, 30, 180):
        config[field] = value
        assert (await create_audience("Test", function_type, config))["ok"] is True
    for value in (0, 181, -1, True, "30", None, float("inf"), float("nan")):
        config[field] = value
        result = await create_audience("Test", function_type, config, dry_run=False)
        assert result["ok"] is False
        assert result["error_code"] == "VALIDATION_ERROR"
        assert field in result["message"]


async def test_lookalike_nested_rules_and_rate(no_client):
    for rate in (0, 0.15):
        config = {"source": {"audienceGroupId": 123}, "volumeRate": {"rate": rate}}
        assert (await create_audience("Test", "LOOKALIKE", config))["ok"] is True
    for config in (
        {"source": {}, "volumeRate": {}},
        {"source": {"audienceGroupId": True}, "volumeRate": {}},
        {"source": {"audienceGroupId": "123"}, "volumeRate": {}},
        {"source": {"audienceGroupId": 123, "available": True}, "volumeRate": {}},
        {"source": {"audienceGroupId": 123, "unavailableReason": "DELETED"}, "volumeRate": {}},
        {"source": [], "volumeRate": {}},
        {"source": {"audienceGroupId": 123}, "volumeRate": {"typo": 1}},
        {"source": {"audienceGroupId": 123}, "volumeRate": {"auto": "true"}},
        *({"source": {"audienceGroupId": 123}, "volumeRate": {"rate": rate}}
          for rate in (-0.01, 0.151, True, "0.05", float("inf"), float("nan"))),
    ):
        result = await create_audience("Test", "LOOKALIKE", config, dry_run=False)
        assert result["ok"] is False
        assert result["error_code"] == "VALIDATION_ERROR"


CONDITIONS = {
    "WEBTRAFFIC": {"conditionType": "CONTAIN", "keywords": ["https://example.com"]},
    "APP_EVENT": {"parameterKey": "ITEM_IDS", "conditionType": "EQUAL_TO", "values": ["item-1"]},
}


@pytest.mark.parametrize("function_type", CONDITIONS)
async def test_condition_group_nested_validation(function_type, no_client):
    config = deepcopy(EXAMPLES[function_type][1])
    condition = CONDITIONS[function_type]
    config["conditionGroup"] = [deepcopy(condition)]
    assert (await create_audience("Test", function_type, config))["ok"] is True
    invalid = [None, "condition", {**condition, "typo": 1}, {**condition, "conditionType": "TYPO"}]
    invalid.extend({key: value for key, value in condition.items() if key != removed} for removed in condition)
    array_key = "keywords" if function_type == "WEBTRAFFIC" else "values"
    invalid.extend({**condition, array_key: value} for value in ("not-array", [1], [None]))
    if function_type == "APP_EVENT":
        invalid.append({**condition, "parameterKey": "TYPO"})
    for value in invalid:
        config["conditionGroup"] = [value]
        result = await create_audience("Test", function_type, config, dry_run=False)
        assert result["ok"] is False
        assert result["error_code"] == "VALIDATION_ERROR"
        assert "config.conditionGroup[0]" in result["message"]
    config["conditionGroup"] = {}
    assert (await create_audience("Test", function_type, config))["ok"] is False


@pytest.mark.parametrize("field,values", [
    ("parameterKey", "CATEGORY_IDS ITEM_IDS ITEM_PRICE ITEM_QUANTITY SEARCH_KEYWORDS LEVEL_IDS DATA EVENT_NAMES"),
    ("conditionType", "EQUAL_TO NOT_EQUAL_TO CONTAIN NOT_CONTAIN PREFIX SUFFIX GREATER_THAN LESS_THAN GREATER_THAN_OR_EQ LESS_THAN_OR_EQ"),
])
async def test_app_condition_enums(field, values, no_client):
    for value in values.split():
        config = {**EXAMPLES["APP_EVENT"][1], "conditionGroup": [{**CONDITIONS["APP_EVENT"], field: value}]}
        assert (await create_audience("Test", "APP_EVENT", config))["ok"] is True


async def test_optional_fields_and_read_only_rejection(no_client):
    for condition_type in ("EQUAL_TO", "CONTAIN", "NOT_CONTAIN"):
        config = {
            "tagId": "shared-tag", "visitType": "URL_MATCHING", "retentionDays": 180,
            "matchingType": "NORMAL", "tagEventType": "CUSTOM_EVENT", "customEventName": "Purchase",
            "conditionGroup": [{"conditionType": condition_type, "keywords": ["/shop"]}],
        }
        assert (await create_audience("Test", "WEBTRAFFIC", config))["payload"]["webtraffic"] == config
    for value in ("name", 123):
        config = {**EXAMPLES["WEBTRAFFIC"][1], "tagOwnerName": value}
        assert (await create_audience("Test", "WEBTRAFFIC", config))["ok"] is False
    assert (await create_audience("Test", "APP_EVENT", {**EXAMPLES["APP_EVENT"][1], "mobileAppId": 123}))["ok"] is True
    for kind, field in (("APP_EVENT", "mobileAppId"), ("VIDEO_VIEW", "mediaVideoId"), ("IMAGE_CLICK", "campaignId")):
        for value in (True, "123", None):
            config = {**EXAMPLES[kind][1], field: value}
            assert (await create_audience("Test", kind, config, dry_run=False))["error_code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("function_type", ["UPLOAD", "CUSTOMER_LIST", "upload_phone", "CUSTOMER-LIST", "customer_list", "IFA_UPLOAD"])
async def test_customer_upload_rejected(function_type, no_client):
    result = await create_audience("Test", function_type, {}, dry_run=False)
    assert result["error_code"] == "VALIDATION_ERROR"
    assert "LINE Ads Manager" in result["message"]
    assert "ไม่รองรับอัปโหลดรายชื่อลูกค้า" in result["message"]


@pytest.mark.parametrize("function_type", ["WEBSITE", "APP", "ENGAGEMENT", "INVALID", None, []])
async def test_unsupported_type_rejected(function_type, no_client):
    assert (await create_audience("Test", function_type, {}, dry_run=False))["error_code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("estimated_size", ["-", "100 or fewer", "1234"])
async def test_accepted_202_posts_once_and_logs_without_readback(monkeypatch, tmp_path, estimated_size):
    calls = []
    # JSON body returned by the API's 202 Accepted response.
    accepted = {"id": 123, "status": "IN_PROGRESS", "estimatedAudienceSize": estimated_size}

    async def fake_post(self, path, json_body):
        calls.append((path, deepcopy(json_body)))
        return accepted

    async def forbidden_get(*args, **kwargs):
        pytest.fail("Audience creation must not poll or read back")

    monkeypatch.setattr(LineAdsClient, "post", fake_post)
    monkeypatch.setattr(LineAdsClient, "get", forbidden_get)
    config = EXAMPLES["ACCOUNT_FRIENDS"][1]
    result = await create_audience("Test", "ACCOUNT_FRIENDS", config, dry_run=False, workspace_dir=str(tmp_path))
    payload = {"name": "Test", "functionType": "ACCOUNT_FRIENDS", "accountFriends": config}
    assert calls == [(ENDPOINT, payload)]
    assert result["ok"] is True
    assert result["data"] == {
        "audience": accepted, "id": 123, "status": "IN_PROGRESS", "estimated_audience_size": estimated_size,
        "note": "LINE กำลังสร้าง audience (IN_PROGRESS) ใช้ใน ad set ได้เมื่อ status = READY — ตรวจด้วย list_audiences",
    }
    lines = (tmp_path / "line-ads-data" / "change_log.jsonl").read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["tool"] == "create_audience"
    assert record["entity_type"] == "audience"
    assert record["entity_id"] == 123
    assert record["ad_account_id"] == "A01887296807"
    assert record["endpoint"] == ENDPOINT
    assert record["payload"] == payload
    assert record["after"] == accepted
    assert record["ok"] is True
    assert record["readback_ok"] is None
    assert record["ts"]


async def test_create_error_has_no_retry(monkeypatch):
    calls = []

    async def fake_post(self, path, json_body):
        calls.append(path)
        raise LineAdsAPIError(429, "rate limit", "RATE_LIMIT")

    monkeypatch.setattr(LineAdsClient, "post", fake_post)
    result = await create_audience("Test", "ACCOUNT_FRIENDS", {"friendStatus": "ACTIVE"}, dry_run=False)
    assert result["ok"] is False
    assert result["error_code"] == "RATE_LIMIT"
    assert calls == [ENDPOINT]


@pytest.mark.parametrize("status_code", [202, 429])
async def test_transport_accepts_202_and_never_retries_429(monkeypatch, status_code):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(status_code, json={"id": 123, "status": "IN_PROGRESS", "estimatedAudienceSize": "-"})

    original_http_client = httpx.AsyncClient

    def mock_http_client(**kwargs):
        return original_http_client(transport=httpx.MockTransport(respond), **kwargs)

    # Exercise the shared client's real retry path over an in-memory transport.
    monkeypatch.setattr(LineAdsClient, "request", ORIGINAL_REQUEST)
    monkeypatch.setattr(httpx, "AsyncClient", mock_http_client)
    result = await create_audience("Test", "ACCOUNT_FRIENDS", {"friendStatus": "ACTIVE"}, dry_run=False)
    assert len(calls) == 1
    assert calls[0].method == "POST"
    if status_code == 202:
        assert result["ok"] is True
        assert result["data"]["status"] == "IN_PROGRESS"
        assert result["data"]["estimated_audience_size"] == "-"
    else:
        assert result["ok"] is False
        assert result["status_code"] == 429
        assert result["error_code"] == "RATE_LIMIT"


async def test_account_override(monkeypatch):
    calls = []

    async def fake_post(self, path, json_body):
        calls.append(path)
        return {"id": 123, "status": "IN_PROGRESS"}

    monkeypatch.setattr(LineAdsClient, "post", fake_post)
    result = await create_audience("Test", "ACCOUNT_FRIENDS", {"friendStatus": "ACTIVE"}, ad_account_id="other", dry_run=False)
    assert calls == ["/adaccounts/other/custom-audiences"]
    assert result["data"]["estimated_audience_size"] is None


@pytest.mark.parametrize("envelope", ["audienceGroups", "datas"])
async def test_list_paging_and_normalization(monkeypatch, envelope):
    calls = []
    rows = [
        {"id": i, "name": f"audience {i}", "functionType": "WEBTRAFFIC", "status": "IN_PROGRESS", "estimatedAudienceSize": "-"}
        for i in range(100)
    ] + [
        {"id": 100, "name": "Friends", "functionType": "ACCOUNT_FRIENDS", "accountFriends": {"friendStatus": "ACTIVE"}, "status": "READY", "estimatedAudienceSize": "100 or fewer"},
        {"id": 101, "name": "Failed", "functionType": "LOOKALIKE", "status": "FAILED", "failedType": "SOURCE_AUDIENCE_TOO_SMALL", "estimatedAudienceSize": "1234"},
        {"id": 102, "name": "Expired", "status": "EXPIRED"},
        {"id": 103, "name": "Unknown"},
    ]

    async def fake_get(self, path, params=None):
        calls.append((path, params))
        page = params["page"]
        return {envelope: rows[(page - 1) * 100:page * 100], "paging": {"totalElements": len(rows)}}

    monkeypatch.setattr(LineAdsClient, "get", fake_get)
    result = await list_audiences()
    assert result["ok"] is True
    data = result["data"]
    assert calls == [(ENDPOINT, {"page": 1, "size": 100}), (ENDPOINT, {"page": 2, "size": 100})]
    assert len(data["audiences"]) == 104
    assert data["active_friends_audience_id"] == 100
    assert "excluded_audience_ids" in data["hint"]
    assert data["paging"]["complete"] is True
    assert data["audiences"][0]["usable_in_adset"] is False
    assert data["audiences"][0]["estimated_audience_size"] == "-"
    ready = data["audiences"][100]
    assert ready == {**rows[100], "function_type": "ACCOUNT_FRIENDS", "estimated_audience_size": "100 or fewer", "usable_in_adset": True}
    failed = data["audiences"][101]
    assert failed["failed_type"] == "SOURCE_AUDIENCE_TOO_SMALL"
    assert failed["estimated_audience_size"] == "1234"
    assert all(not row["usable_in_adset"] for row in data["audiences"][101:])
    assert "failed_type" not in ready


@pytest.mark.parametrize("body", [{"audienceGroups": []}, {"datas": []}, [], [{"id": 1, "name": "legacy"}]])
async def test_list_legacy_shapes_and_no_active_friends(monkeypatch, body):
    async def fake_get(self, path, params=None):
        return body

    monkeypatch.setattr(LineAdsClient, "get", fake_get)
    result = await list_audiences("other")
    assert result["ok"] is True
    assert result["data"]["active_friends_audience_id"] is None
    assert result["data"]["paging"]["complete"] is True


async def test_registry_uses_creatable_function_types():
    from line_ads_mcp.server import TOOLS

    schema = TOOLS["create_audience"][1]
    assert set(schema["properties"]["function_type"]["enum"]) == AUDIENCE_FUNCTION_TYPES == set(EXAMPLES)
    assert schema["required"] == ["name", "function_type", "config"]
    assert "type" not in schema["properties"]
