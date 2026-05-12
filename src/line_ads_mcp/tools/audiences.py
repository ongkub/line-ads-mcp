"""Custom audience tools."""

from __future__ import annotations

from typing import Any

from line_ads_mcp.client import LineAdsClient, LineAdsConfig, resolve_ad_account_id

from .common import dry_run_response, handle_tool_error, ok, require_one_of

AUDIENCE_TYPES = {"CUSTOMER_LIST", "WEBSITE", "APP", "ENGAGEMENT"}


async def list_audiences(ad_account_id: str | None = None) -> dict[str, Any]:
    """List all custom audiences.

    Verified: API returns audienceGroups key (not datas).
    ACCOUNT_FRIENDS + friendStatus=ACTIVE audience must be used as
    excludedCustomAudienceIds when creating adsets for GAIN_FRIENDS campaigns.
    """
    try:
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        async with LineAdsClient(config) as client:
            data = await client.get(f"/adaccounts/{account_id}/custom-audiences")
        # Normalize: API returns audienceGroups, not datas
        audiences = data.get("audienceGroups", []) if isinstance(data, dict) else data

        # แสดง active friends audience ชัดเจน เพื่อให้ง่ายต่อการใช้ใน create_adset
        active_friends = [
            a for a in audiences
            if a.get("functionType") == "ACCOUNT_FRIENDS"
            and a.get("accountFriends", {}).get("friendStatus") == "ACTIVE"
        ]
        return ok({
            "audiences": audiences,
            "active_friends_audience_id": active_friends[0]["id"] if active_friends else None,
            "hint": "ใช้ active_friends_audience_id เป็น excluded_audience_ids ใน create_adset สำหรับ GAIN_FRIENDS campaigns",
        })
    except Exception as error:
        return handle_tool_error(error)


async def create_audience(
    name: str,
    type: str,
    ad_account_id: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    try:
        require_one_of(type, AUDIENCE_TYPES, "type")
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        payload = {"name": name, "type": type}
        endpoint = f"/adaccounts/{account_id}/custom-audiences"
        if dry_run:
            return dry_run_response("create_audience", endpoint, payload)
        async with LineAdsClient(config) as client:
            data = await client.post(endpoint, payload)
        return ok(data)
    except Exception as error:
        return handle_tool_error(error)

