"""Ad set/adgroup tools."""

from __future__ import annotations

from typing import Any

from line_ads_mcp.client import LineAdsClient, LineAdsConfig, resolve_ad_account_id

from .common import clean_dict, dry_run_response, handle_tool_error, ok, require_one_of, to_micro

STATUSES = {"ACTIVE", "PAUSED"}
# Confirmed from real adset data: bidType: CPF, bidStrategy: COST_CAP
BID_TYPES = {"CPF", "CPM", "CPC", "CPV"}
BID_STRATEGIES = {"COST_CAP", "LOWEST_COST"}


async def list_adsets(campaign_id: str, ad_account_id: str | None = None) -> dict[str, Any]:
    try:
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        async with LineAdsClient(config) as client:
            data = await client.get(f"/adaccounts/{account_id}/adgroups", params={"campaignId": campaign_id})
        return ok(data)
    except Exception as error:
        return handle_tool_error(error)


async def create_adset(
    campaign_id: str,
    name: str,
    bid_type: str,
    bid_strategy: str,
    ad_account_id: str | None = None,
    daily_budget: float | None = None,
    bid_amount: float | None = None,
    targeting: dict[str, Any] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    try:
        require_one_of(bid_type, BID_TYPES, "bid_type")
        require_one_of(bid_strategy, BID_STRATEGIES, "bid_strategy")
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        payload = clean_dict(
            {
                "campaignId": campaign_id,
                "name": name,
                "bidType": bid_type,
                "bidStrategy": bid_strategy,
                "dailyBudgetMicro": to_micro(daily_budget) if daily_budget is not None else None,
                "bidAmountMicro": to_micro(bid_amount) if bid_amount is not None else None,
                "targeting": targeting,
                "startDate": start_date,
                "endDate": end_date,
            }
        )
        endpoint = f"/adaccounts/{account_id}/adgroups"
        if dry_run:
            return dry_run_response("create_adset", endpoint, payload)
        async with LineAdsClient(config) as client:
            data = await client.post(endpoint, payload)
        return ok(data)
    except Exception as error:
        return handle_tool_error(error)


async def update_adset(
    adset_id: str,
    ad_account_id: str | None = None,
    status: str | None = None,
    daily_budget: float | None = None,
    bid_amount: float | None = None,
    targeting: dict[str, Any] | None = None,
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
                "bidAmountMicro": to_micro(bid_amount) if bid_amount is not None else None,
                "targeting": targeting,
            }
        )
        endpoint = f"/adaccounts/{account_id}/adgroups/{adset_id}"
        if dry_run:
            return dry_run_response("update_adset", endpoint, payload)
        async with LineAdsClient(config) as client:
            data = await client.put(endpoint, payload)
        return ok(data)
    except Exception as error:
        return handle_tool_error(error)


async def pause_adset(
    adset_id: str,
    ad_account_id: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    return await update_adset(adset_id, ad_account_id, status="PAUSED", dry_run=dry_run)


async def resume_adset(
    adset_id: str,
    ad_account_id: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    return await update_adset(adset_id, ad_account_id, status="ACTIVE", dry_run=dry_run)
