"""Custom audience tools for LINE Ads API v3.12.3."""

from __future__ import annotations

import math
from typing import Any

import httpx

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient, LineAdsConfig, resolve_ad_account_id

from .change_log import set_change_context, track_change
from .common import dry_run_response, handle_tool_error, ok, require_one_of
from .paging import fetch_all_pages

# Compatibility export: older contract consumers still import this name.
AUDIENCE_TYPES = {"CUSTOMER_LIST", "WEBSITE", "APP", "ENGAGEMENT"}
AUDIENCE_CONFIG_KEYS = {
    "LOOKALIKE": "lookalike", "APP_EVENT": "appEvent", "WEBTRAFFIC": "webtraffic",
    "ACCOUNT_FRIENDS": "accountFriends", "VIDEO_VIEW": "videoView", "IMAGE_CLICK": "imageClick",
}
AUDIENCE_FUNCTION_TYPES = set(AUDIENCE_CONFIG_KEYS)


def _rule(kind: Any, required: bool = False, **constraints: Any) -> dict[str, Any]:
    return {"type": kind, "required": required, **constraints}


_NUMBER = (int, float)
AUDIENCE_CONFIG_RULES = {
    "WEBTRAFFIC": {
        "tagId": _rule(str),
        "visitType": _rule(str, True, enum={"VISIT_ALL", "URL_MATCHING", "EVENT_MATCHING"}),
        "retentionDays": _rule(_NUMBER, True, minimum=1, maximum=180),
        "matchingType": _rule(str, enum={"NONE", "NORMAL"}),
        "conditionGroup": _rule(list, items=_rule(dict, fields={
            "conditionType": _rule(str, True, enum={"EQUAL_TO", "CONTAIN", "NOT_CONTAIN"}),
            "keywords": _rule(list, True, items=_rule(str)),
        })),
        "tagEventType": _rule(str, enum={"CONVERSION_EVENT", "CUSTOM_EVENT"}),
        "customEventName": _rule(str),
    },
    "LOOKALIKE": {
        "source": _rule(dict, True, fields={"audienceGroupId": _rule(_NUMBER, True)}),
        "volumeRate": _rule(dict, True, fields={
            "auto": _rule(bool), "rate": _rule(_NUMBER, minimum=0, maximum=0.15),
        }),
    },
    "APP_EVENT": {
        "mobileAppId": _rule(_NUMBER),
        "actionType": _rule(str, True, enum=set((
            "INSTALL OPEN ADD_TO_CART PURCHASE VIEW_HOME VIEW_CATEGORY VIEW_ITEM SEARCH "
            "LEVEL_ACHIEVED TUTORIAL_COMPLETE CUSTOM"
        ).split())),
        "retentionDays": _rule(_NUMBER, True, minimum=1, maximum=180),
        "matchMethod": _rule(str, True, enum={"NONE", "NORMAL"}),
        "conditionGroup": _rule(list, items=_rule(dict, fields={
            "parameterKey": _rule(str, True, enum=set((
                "CATEGORY_IDS ITEM_IDS ITEM_PRICE ITEM_QUANTITY SEARCH_KEYWORDS LEVEL_IDS DATA EVENT_NAMES"
            ).split())),
            "conditionType": _rule(str, True, enum=set((
                "EQUAL_TO NOT_EQUAL_TO CONTAIN NOT_CONTAIN PREFIX SUFFIX GREATER_THAN "
                "LESS_THAN GREATER_THAN_OR_EQ LESS_THAN_OR_EQ"
            ).split())),
            "values": _rule(list, True, items=_rule(str)),
        })),
    },
    "ACCOUNT_FRIENDS": {
        "friendStatus": _rule(str, True, enum={"ACTIVE", "BLOCKED"}),
    },
    "VIDEO_VIEW": {
        "eventType": _rule(str, True, enum=set((
            "CLICK PLAY_START VIDEO_PLAY_3S VIDEO_PLAY_25P VIDEO_PLAY_50P VIDEO_PLAY_75P "
            "VIDEO_PLAY_95P VIDEO_PLAY_COMPLETED"
        ).split())),
        "mediaVideoId": _rule(_NUMBER, True),
        "recency": _rule(_NUMBER, True, minimum=1, maximum=180),
    },
    "IMAGE_CLICK": {
        "eventType": _rule(str, True, enum={"CLICK"}),
        "campaignId": _rule(_NUMBER, True),
        "recency": _rule(_NUMBER, True, minimum=1, maximum=180),
    },
}


def _invalid(path: str, reason: str) -> None:
    raise LineAdsAPIError(400, f"{path}: {reason}", "VALIDATION_ERROR")


def _validate(value: Any, rule: dict[str, Any], path: str) -> None:
    kind = rule["type"]
    if not isinstance(value, kind) or (kind == _NUMBER and isinstance(value, bool)):
        _invalid(path, "ชนิดข้อมูลไม่ถูกต้อง")
    if kind == _NUMBER:
        if isinstance(value, float) and not math.isfinite(value):
            _invalid(path, "ต้องเป็นตัวเลข finite")
        if "minimum" in rule and value < rule["minimum"]:
            _invalid(path, f"ต้องไม่น้อยกว่า {rule['minimum']}")
        if "maximum" in rule and value > rule["maximum"]:
            _invalid(path, f"ต้องไม่เกิน {rule['maximum']}")
    if "enum" in rule and value not in rule["enum"]:
        _invalid(path, f"ต้องเป็นค่าใดค่าหนึ่ง: {', '.join(sorted(rule['enum']))}")
    if kind is dict:
        fields = rule["fields"]
        for key in value:
            if key not in fields:
                _invalid(f"{path}.{key}", "ไม่รองรับฟิลด์นี้")
        for key, child in fields.items():
            if key not in value:
                if child["required"]:
                    _invalid(f"{path}.{key}", "จำเป็นต้องระบุ")
            else:
                _validate(value[key], child, f"{path}.{key}")
    if kind is list:
        for index, item in enumerate(value):
            _validate(item, rule["items"], f"{path}[{index}]")


class _AudiencePages:
    """Adapt the audienceGroups envelope to the shared paging helper."""

    def __init__(self, client: LineAdsClient):
        self.client = client

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        data = await self.client.get(path, params=params)
        if isinstance(data, list):
            return {"datas": data}
        if isinstance(data, dict) and "datas" not in data and "audienceGroups" in data:
            return {**data, "datas": data["audienceGroups"]}
        return data


async def list_audiences(ad_account_id: str | None = None) -> dict[str, Any]:
    """List all pages, preserving raw fields and adding normalized readiness."""
    try:
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        async with LineAdsClient(config) as client:
            result = await fetch_all_pages(_AudiencePages(client), f"/adaccounts/{account_id}/custom-audiences")
        aliases = {
            "functionType": "function_type", "estimatedAudienceSize": "estimated_audience_size",
            "failedType": "failed_type",
        }
        audiences = [
            {**row, **{target: row[source] for source, target in aliases.items() if source in row},
             "usable_in_adset": row.get("status") == "READY"}
            for row in result["datas"]
        ]
        active_friends = [
            a for a in audiences
            if a.get("functionType") == "ACCOUNT_FRIENDS"
            and a.get("accountFriends", {}).get("friendStatus") == "ACTIVE"
        ]
        return ok({
            "audiences": audiences,
            "active_friends_audience_id": active_friends[0].get("id") if active_friends else None,
            "hint": "ใช้ active_friends_audience_id เป็น excluded_audience_ids ใน create_adset สำหรับ GAIN_FRIENDS campaigns",
            "paging": result["paging"],
        })
    except Exception as error:
        return handle_tool_error(error)


async def _reject_rate_limit(response: httpx.Response) -> None:
    """Stop the shared client's 429 retries for this non-idempotent create."""
    if response.status_code == 429:
        raise LineAdsAPIError(429, "LINE Ads API rate limit ครับ ลองใหม่อีกครั้งภายหลัง", "RATE_LIMIT")


@track_change("audience")
async def create_audience(
    name: str,
    function_type: str,
    config: dict[str, Any],
    ad_account_id: str | None = None,
    dry_run: bool = True,
    workspace_dir: str | None = None,
) -> dict[str, Any]:
    """Validate a creatable audience; a successful POST only accepts creation."""
    try:
        _validate(function_type, _rule(str), "function_type")
        upload_type = function_type.upper().replace("-", "_")
        if "UPLOAD" in upload_type or upload_type.replace("_", "") == "CUSTOMERLIST":
            _invalid("function_type", "ไม่รองรับอัปโหลดรายชื่อลูกค้า กรุณาใช้ LINE Ads Manager โดยอัปโหลดด้วยตนเอง")
        require_one_of(function_type, AUDIENCE_FUNCTION_TYPES, "function_type")
        _validate(config, _rule(dict, fields=AUDIENCE_CONFIG_RULES[function_type]), "config")
        client_config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, client_config)
        payload = {"name": name, "functionType": function_type, AUDIENCE_CONFIG_KEYS[function_type]: config}
        endpoint = f"/adaccounts/{account_id}/custom-audiences"
        if dry_run:
            return dry_run_response("create_audience", endpoint, payload)
        set_change_context(ad_account_id=account_id, endpoint=endpoint, payload=payload)
        async with httpx.AsyncClient(timeout=30, event_hooks={"response": [_reject_rate_limit]}) as http_client:
            async with LineAdsClient(client_config, http_client=http_client) as client:
                data = await client.post(endpoint, payload)
        set_change_context(entity_id=data.get("id"), after=data)
        return ok({
            "audience": data,
            "id": data.get("id"),
            "status": data.get("status"),
            "estimated_audience_size": data.get("estimatedAudienceSize"),
            "note": "LINE กำลังสร้าง audience (IN_PROGRESS) ใช้ใน ad set ได้เมื่อ status = READY — ตรวจด้วย list_audiences",
        })
    except Exception as error:
        return handle_tool_error(error)
