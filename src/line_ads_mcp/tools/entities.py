"""Entity lookup and inspection tools."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient, LineAdsConfig, resolve_ad_account_id

from .common import handle_tool_error, ok, require_one_of

ENTITY_TYPE_ENDPOINTS: dict[str, str] = {
    "campaign": "campaigns",
    "adset": "adgroups",
    "ad": "ads",
}
VALID_ENTITY_TYPES = set(ENTITY_TYPE_ENDPOINTS.keys())


def _extract_review(row: dict[str, Any]) -> Any:
    if row.get("review") is not None:
        return row["review"]
    review_fields = {k: v for k, v in row.items() if "review" in k.lower()}
    if review_fields:
        return review_fields
    return None


def _extract_budget(row: dict[str, Any]) -> dict[str, Any]:
    budget: dict[str, Any] = {}
    for key, value in row.items():
        if "budget" in key.lower():
            budget[key] = value
            if "micro" in key.lower() and isinstance(value, (int, float)):
                thb = value / 1_000_000
                base_key = re.sub(r"(?i)micro$", "", key)
                snake_base = re.sub(r"(?<!^)(?=[A-Z])", "_", base_key).lower()
                budget[f"{snake_base}_thb"] = thb
    return budget


def _extract_bid(row: dict[str, Any]) -> dict[str, Any]:
    bid: dict[str, Any] = {}
    for key, value in row.items():
        if "bid" in key.lower():
            bid[key] = value
            if "micro" in key.lower() and isinstance(value, (int, float)):
                thb = value / 1_000_000
                base_key = re.sub(r"(?i)micro$", "", key)
                snake_base = re.sub(r"(?<!^)(?=[A-Z])", "_", base_key).lower()
                bid[f"{snake_base}_thb"] = thb
    return bid


async def fetch_entity(
    client: LineAdsClient,
    account_id: str,
    entity_type: str,
    entity_id: str | int,
) -> dict[str, Any] | None:
    require_one_of(entity_type, VALID_ENTITY_TYPES, "entity_type")
    endpoint = f"/adaccounts/{account_id}/{ENTITY_TYPE_ENDPOINTS[entity_type]}"
    data = await client.get(endpoint, params={"ids": entity_id, "includeRemoved": "true"})
    if isinstance(data, dict):
        datas = data.get("datas")
        if isinstance(datas, list):
            for row in datas:
                if isinstance(row, dict) and str(row.get("id")) == str(entity_id):
                    return row
    return None


async def get_entity(
    entity_type: str,
    entity_id: str | int,
    ad_account_id: str | None = None,
) -> dict[str, Any]:
    try:
        require_one_of(entity_type, VALID_ENTITY_TYPES, "entity_type")
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        async with LineAdsClient(config) as client:
            row = await fetch_entity(client, account_id, entity_type, entity_id)

        if row is None:
            raise LineAdsAPIError(404, f"ไม่พบ {entity_type} ID: {entity_id}", "NOT_FOUND")

        return ok({
            "entity_type": entity_type,
            "id": row.get("id"),
            "name": row.get("name"),
            "configured_status": row.get("configuredStatus"),
            "delivery_status": row.get("deliveryStatus"),
            "review": _extract_review(row),
            "budget": _extract_budget(row),
            "bid": _extract_bid(row),
            "targeting": row.get("targeting"),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "raw": row,
        })
    except Exception as error:
        return handle_tool_error(error)
