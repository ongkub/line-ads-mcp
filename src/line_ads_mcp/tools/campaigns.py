"""Campaign tools."""

from __future__ import annotations

from typing import Any

from line_ads_mcp.client import LineAdsClient, LineAdsConfig, resolve_ad_account_id

from .common import clean_dict, dry_run_response, handle_tool_error, ok, require_one_of, to_micro

# Confirmed from real API smoke test: response uses campaignObjective: GAIN_FRIENDS
OBJECTIVES = {
    "GAIN_FRIENDS",
    "WEBSITE_TRAFFIC",
    "CONVERSIONS",
    "REACH",
    "APP_INSTALL",
    "VIDEO_VIEW",
}
STATUSES = {"ACTIVE", "PAUSED"}


async def list_campaigns(
    ad_account_id: str | None = None,
    page: int = 1,
    size: int = 20,
) -> dict[str, Any]:
    try:
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        params = {"page": page, "size": min(size, 500)}
        async with LineAdsClient(config) as client:
            data = await client.get(f"/adaccounts/{account_id}/campaigns", params=params)
        return ok(data)
    except Exception as error:
        return handle_tool_error(error)


async def create_campaign(
    name: str,
    objective: str,
    ad_account_id: str | None = None,
    daily_budget: float | None = None,
    total_budget: float | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    try:
        require_one_of(objective, OBJECTIVES, "objective")
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        payload = clean_dict(
            {
                "name": name,
                "campaignObjective": objective,
                "dailyBudgetMicro": to_micro(daily_budget) if daily_budget is not None else None,
                "totalBudgetMicro": to_micro(total_budget) if total_budget is not None else None,
                "startDate": start_date,
                "endDate": end_date,
            }
        )
        endpoint = f"/adaccounts/{account_id}/campaigns"
        if dry_run:
            return dry_run_response("create_campaign", endpoint, payload)
        async with LineAdsClient(config) as client:
            data = await client.post(endpoint, payload)
        return ok(data)
    except Exception as error:
        return handle_tool_error(error)


async def update_campaign(
    campaign_id: str,
    ad_account_id: str | None = None,
    status: str | None = None,
    daily_budget: float | None = None,
    name: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    try:
        if status:
            require_one_of(status, STATUSES, "status")
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        payload = clean_dict(
            {
                "configuredStatus": status,
                "dailyBudgetMicro": to_micro(daily_budget) if daily_budget is not None else None,
                "name": name,
            }
        )
        endpoint = f"/adaccounts/{account_id}/campaigns/{campaign_id}"
        if dry_run:
            return dry_run_response("update_campaign", endpoint, payload)
        async with LineAdsClient(config) as client:
            data = await client.post(endpoint, payload)
        return ok(data)
    except Exception as error:
        return handle_tool_error(error)


async def pause_campaign(
    campaign_id: str,
    ad_account_id: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    return await update_campaign(campaign_id, ad_account_id, status="PAUSED", dry_run=dry_run)


async def resume_campaign(
    campaign_id: str,
    ad_account_id: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    return await update_campaign(campaign_id, ad_account_id, status="ACTIVE", dry_run=dry_run)
