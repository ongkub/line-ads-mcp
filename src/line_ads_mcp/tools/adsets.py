"""Ad set/adgroup tools."""

from __future__ import annotations

from typing import Any

from line_ads_mcp.client import LineAdsClient, LineAdsConfig, resolve_ad_account_id

from .common import clean_dict, dry_run_response, handle_tool_error, ok, require_one_of, to_micro

STATUSES = {"ACTIVE", "PAUSED"}
BID_TYPES = {"CPF", "CPM", "CPC", "CPV"}
BID_STRATEGIES = {"COST_CAP", "LOWEST_COST"}
TARGETING_MODES = {"AUTO", "MANUAL"}

# autoBidType verified from real API:
#   CPF + GAIN_FRIENDS → FRIEND (required, or API returns error)
AUTO_BID_TYPES = {"FRIEND", "CLICK", "INSTALL", "VIDEO_VIEW", "REACH"}

# Valid LINE Ads age bracket values for TH (verified by probing)
VALID_AGES = {15, 18, 20, 25, 30, 35, 40, 45, 50, 54, 55, 60, 65}


def _build_targeting(
    *,
    age_min: int,
    age_max: int,
    country: str,
    targeting_mode: str | None = None,
    genders: list[str] | None = None,
    interest_codes: list[str] | None = None,
    excluded_audience_ids: list[str] | None = None,
    custom_audience_ids: list[str] | None = None,
) -> dict[str, Any]:
    has_manual_targeting = bool(genders or interest_codes or custom_audience_ids)
    mode = targeting_mode or ("MANUAL" if has_manual_targeting else "AUTO")
    require_one_of(mode, TARGETING_MODES, "targeting_mode")

    targeting = clean_dict({
        "targetingMode": mode,
        "ageMin": age_min,
        "ageMax": age_max,
        "country": country,
        "genders": genders or None,
        "customAudienceIds": custom_audience_ids or None,
        "excludedCustomAudienceIds": excluded_audience_ids or None,
    })
    if interest_codes:
        targeting["includeAdvancedTargetings"] = [{"interests": interest_codes}]
    return targeting


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
    auto_bid_type: str,
    daily_budget: float,
    ad_account_id: str | None = None,
    bid_amount: float | None = None,
    age_min: int = 20,
    age_max: int = 65,
    country: str = "TH",
    targeting_mode: str | None = None,
    genders: list[str] | None = None,
    interest_codes: list[str] | None = None,
    excluded_audience_ids: list[str] | None = None,
    custom_audience_ids: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Create an adset with verified payload structure.

    Verified from real API:
    - autoBidType is required (FRIEND for CPF/GAIN_FRIENDS campaigns)
    - targeting is always required (flat object with targetingMode, ageMin, ageMax, country)
    - interest targeting must use targetingMode=MANUAL and includeAdvancedTargetings
    - GAIN_FRIENDS campaigns require excludedCustomAudienceIds (existing LINE OA friends audience)
    - bid_amount required only when bid_strategy=COST_CAP
    """
    try:
        require_one_of(bid_type, BID_TYPES, "bid_type")
        require_one_of(bid_strategy, BID_STRATEGIES, "bid_strategy")
        require_one_of(auto_bid_type, AUTO_BID_TYPES, "auto_bid_type")
        if bid_strategy == "COST_CAP" and bid_amount is None:
            from line_ads_mcp.client import LineAdsAPIError
            raise LineAdsAPIError(400, "bid_strategy=COST_CAP ต้องระบุ bid_amount ด้วย", "VALIDATION_ERROR")
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)

        targeting = _build_targeting(
            age_min=age_min,
            age_max=age_max,
            country=country,
            targeting_mode=targeting_mode,
            genders=genders,
            interest_codes=interest_codes,
            excluded_audience_ids=excluded_audience_ids,
            custom_audience_ids=custom_audience_ids,
        )

        payload = clean_dict({
            "campaignId": campaign_id,
            "name": name,
            "bidType": bid_type,
            "bidStrategy": bid_strategy,
            "autoBidType": auto_bid_type,
            "dailyBudgetMicro": to_micro(daily_budget),
            "bidAmountMicro": to_micro(bid_amount) if bid_amount is not None else None,
            "targeting": targeting,
            "startDate": start_date,
            "endDate": end_date,
        })
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
    age_min: int | None = None,
    age_max: int | None = None,
    country: str = "TH",
    targeting_mode: str | None = None,
    genders: list[str] | None = None,
    interest_codes: list[str] | None = None,
    excluded_audience_ids: list[str] | None = None,
    custom_audience_ids: list[str] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    try:
        if status:
            require_one_of(status, STATUSES, "status")
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        if targeting is None and any(
            value is not None
            for value in (age_min, age_max, targeting_mode, genders, interest_codes, excluded_audience_ids, custom_audience_ids)
        ):
            targeting = _build_targeting(
                age_min=age_min if age_min is not None else 20,
                age_max=age_max if age_max is not None else 65,
                country=country,
                targeting_mode=targeting_mode,
                genders=genders,
                interest_codes=interest_codes,
                excluded_audience_ids=excluded_audience_ids,
                custom_audience_ids=custom_audience_ids,
            )
        payload = clean_dict({
            "configuredStatus": status,
            "dailyBudgetMicro": to_micro(daily_budget) if daily_budget is not None else None,
            "bidAmountMicro": to_micro(bid_amount) if bid_amount is not None else None,
            "targeting": targeting,
        })
        endpoint = f"/adaccounts/{account_id}/adgroups/{adset_id}"
        if dry_run:
            return dry_run_response("update_adset", endpoint, payload)
        async with LineAdsClient(config) as client:
            data = await client.post(endpoint, payload)
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
