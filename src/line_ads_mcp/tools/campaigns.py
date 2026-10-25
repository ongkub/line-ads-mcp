"""Campaign tools."""

from __future__ import annotations

from typing import Any

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient, LineAdsConfig, resolve_ad_account_id

from .common import clean_dict, dry_run_response, handle_tool_error, ok, require_one_of, to_micro
from .paging import fetch_all_pages
from .change_log import preview_update, track_change, write_entity

# Confirmed from real accounts (2026-10-25): GAIN_FRIENDS, VISIT_MY_WEBSITE, WEBSITE_CONVERSION, REACH.
# APP_INSTALL / VIDEO_VIEW are unverified. Older names used by this repo are accepted as aliases.
OBJECTIVES = {
    "GAIN_FRIENDS",
    "VISIT_MY_WEBSITE",
    "WEBSITE_CONVERSION",
    "REACH",
    "APP_INSTALL",
    "VIDEO_VIEW",
}
OBJECTIVE_ALIASES = {
    "WEBSITE_TRAFFIC": "VISIT_MY_WEBSITE",
    "CONVERSIONS": "WEBSITE_CONVERSION",
}


def normalize_objective(objective: str) -> str:
    """Map legacy objective names to the values the LINE Ads API returns."""
    return OBJECTIVE_ALIASES.get(objective, objective)
STATUSES = {"ACTIVE", "PAUSED"}
CAMPAIGN_STATUS_FILTER = {"ACTIVE", "PAUSED", "REMOVED"}


async def list_campaigns(
    ad_account_id: str | None = None,
    status: str | None = None,
    fetch_all: bool = True,
    page: int = 1,
    size: int = 100,
) -> dict[str, Any]:
    try:
        if status is not None:
            require_one_of(status, CAMPAIGN_STATUS_FILTER, "status")
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        path = f"/adaccounts/{account_id}/campaigns"
        params: dict[str, Any] = {}
        if status == "REMOVED":
            params["includeRemoved"] = "true"

        async with LineAdsClient(config) as client:
            if fetch_all:
                result = await fetch_all_pages(client, path, params=params, page_size=size)
                datas = result.get("datas", [])
                paging = result.get("paging", {})
            else:
                p = dict(params)
                p["page"] = page
                p["size"] = size
                data = await client.get(path, params=p)
                datas = data.get("datas", []) if isinstance(data, dict) else []
                paging = data.get("paging", {}) if isinstance(data, dict) else {}

        if status is not None:
            datas = [row for row in datas if isinstance(row, dict) and row.get("configuredStatus") == status]

        return ok({"datas": datas, "paging": paging, "status_filter": status})
    except Exception as error:
        return handle_tool_error(error)


@track_change("campaign")
async def create_campaign(
    name: str,
    objective: str,
    ad_account_id: str | None = None,
    daily_budget: float | None = None,
    total_budget: float | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    dry_run: bool = True,
    status: str = "PAUSED",
    workspace_dir: str | None = None,
) -> dict[str, Any]:
    try:
        require_one_of(status, {"PAUSED", "ACTIVE"}, "status")
        objective = normalize_objective(objective)
        require_one_of(objective, OBJECTIVES, "objective")
        if not start_date:
            raise LineAdsAPIError(
                400,
                "start_date เป็นข้อมูลจำเป็น กรุณาถาม user และระบุวันเวลาเริ่มโฆษณาก่อนสร้าง campaign",
                "VALIDATION_ERROR",
            )
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        payload = clean_dict(
            {
                "name": name,
                "configuredStatus": status,
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
        return await write_entity(config, account_id, "campaign", endpoint, payload)
    except Exception as error:
        return handle_tool_error(error)


@track_change("campaign", "campaign_id")
async def update_campaign(
    campaign_id: str,
    ad_account_id: str | None = None,
    status: str | None = None,
    daily_budget: float | None = None,
    name: str | None = None,
    dry_run: bool = True,
    workspace_dir: str | None = None,
) -> dict[str, Any]:
    try:
        if status is not None:
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
            return await preview_update(config, account_id, "campaign", "update_campaign", endpoint, payload, campaign_id)
        return await write_entity(config, account_id, "campaign", endpoint, payload, campaign_id)
    except Exception as error:
        return handle_tool_error(error)


@track_change("campaign", "campaign_id")
async def pause_campaign(
    campaign_id: str,
    ad_account_id: str | None = None,
    dry_run: bool = True,
    workspace_dir: str | None = None,
) -> dict[str, Any]:
    return await update_campaign(campaign_id, ad_account_id, status="PAUSED", dry_run=dry_run, workspace_dir=workspace_dir)


@track_change("campaign", "campaign_id")
async def resume_campaign(
    campaign_id: str,
    ad_account_id: str | None = None,
    dry_run: bool = True,
    workspace_dir: str | None = None,
) -> dict[str, Any]:
    return await update_campaign(campaign_id, ad_account_id, status="ACTIVE", dry_run=dry_run, workspace_dir=workspace_dir)
