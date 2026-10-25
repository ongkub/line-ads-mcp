"""Ad set/adgroup tools."""

from __future__ import annotations

from typing import Any

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient, LineAdsConfig, resolve_ad_account_id

from .common import clean_dict, dry_run_response, handle_tool_error, ok, require_one_of, to_micro
from .paging import fetch_all_pages
from .change_log import preview_update, track_change, write_entity

STATUSES = {"ACTIVE", "PAUSED"}
ADSET_STATUS_FILTER = {"ACTIVE", "PAUSED", "REMOVED"}
BID_TYPES = {"CPF", "CPM", "CPC", "CPV"}
BID_STRATEGIES = {"COST_CAP", "LOWEST_COST"}
TARGETING_MODES = {"AUTO", "MANUAL"}

# autoBidType verified from real API:
#   CPF + GAIN_FRIENDS → FRIEND (required, or API returns error)
AUTO_BID_TYPES = {"FRIEND", "CLICK", "INSTALL", "VIDEO_VIEW", "REACH"}

# Age dropdowns in Ads Manager (TH, verified from UI 2026-09-27):
#   ageMin: 20, 25, ..., 65 (ขั้นละ 5)
#   ageMax: 24, 29, ..., 64 (ขั้นละ 5) หรือ "ไม่ตั้งค่า" = ไม่ส่ง ageMax
# API rejects ageMax=65 (REQUEST_INPUT_AGE_MIN_MAX_REVERSED).
VALID_AGE_MIN = set(range(20, 66, 5))
VALID_AGE_MAX = set(range(24, 65, 5))
# Legacy callers passed 65 meaning "no upper limit"; keep accepting it and send no ageMax.
LEGACY_NO_AGE_MAX = 65


# Selectable codes by type (verified from /codes/advanced-targeting, TH/th, 2026-09-27).
# Every other code is a BEHAVIOR (OA followers, OpenChat, LINE TODAY, app categories, ...).
INTEREST_CODES = {
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "15", "16", "17", "18", "30", "31",
    "1016", "1017", "1018", "1019", "1603", "1604", "1605", "1606", "1607", "1608", "1609", "1610",
    "1611", "1612", "1613", "1614", "1615", "1616", "1617", "1618", "1619", "1620", "1621", "1622",
    "1623", "1624", "1625", "1626", "1627", "1628", "1629", "1630", "1631", "1632", "1634", "1635",
}
PURCHASE_INTENT_CODES = {
    "1021", "1022", "1023", "1024", "1025", "1594", "1595", "1596", "1597", "1598", "1599", "1600",
}


def _split_codes_by_type(codes: list[str]) -> dict[str, list[str]]:
    """Split one targeting layer into the keys LINE expects (interests/behaviors/purchaseIntents)."""
    split: dict[str, list[str]] = {}
    for code in codes:
        if not code:
            continue
        if code in INTEREST_CODES:
            key = "interests"
        elif code in PURCHASE_INTENT_CODES:
            key = "purchaseIntents"
        else:
            key = "behaviors"
        split.setdefault(key, []).append(code)
    return split


def _build_advanced_targeting_groups(
    *,
    interest_codes: list[str] | None = None,
    interest_groups: list[list[str]] | None = None,
    behavior_codes: list[str] | None = None,
) -> list[dict[str, list[str]]]:
    """Build LINE includeAdvancedTargetings groups.

    LINE treats each object in includeAdvancedTargetings as a separate condition.
    Use interest_groups for narrow/intersection-like targeting: each inner list is
    one layer and may mix interest, behavior (e.g. app categories) and purchase
    intent codes, for example
    [["4"], ["12", "2441"]] -> [{"interests": ["4"]}, {"interests": ["12"], "behaviors": ["2441"]}].
    """
    groups: list[dict[str, list[str]]] = []

    for group in interest_groups or []:
        split_group = _split_codes_by_type(group)
        if split_group:
            groups.append(split_group)

    broad_group: dict[str, list[str]] = {}
    if interest_codes:
        broad_group["interests"] = interest_codes
    if behavior_codes:
        broad_group["behaviors"] = behavior_codes
    if broad_group:
        groups.append(broad_group)

    return groups


def _build_targeting(
    *,
    age_min: int,
    age_max: int | None,
    country: str,
    targeting_mode: str | None = None,
    genders: list[str] | None = None,
    interest_codes: list[str] | None = None,
    interest_groups: list[list[str]] | None = None,
    behavior_codes: list[str] | None = None,
    excluded_audience_ids: list[str] | None = None,
    custom_audience_ids: list[str] | None = None,
) -> dict[str, Any]:
    if age_min not in VALID_AGE_MIN:
        raise LineAdsAPIError(
            400,
            f"age_min={age_min} ไม่ถูกต้อง ค่าที่ LINE Ads รองรับ: {sorted(VALID_AGE_MIN)}",
            "VALIDATION_ERROR",
        )
    if age_max == LEGACY_NO_AGE_MAX:
        age_max = None
    if age_max is not None and age_max not in VALID_AGE_MAX:
        raise LineAdsAPIError(
            400,
            f"age_max={age_max} ไม่ถูกต้อง ค่าที่ LINE Ads รองรับ: {sorted(VALID_AGE_MAX)} หรือไม่ระบุ (= ไม่ตั้งค่า)",
            "VALIDATION_ERROR",
        )
    if age_max is not None and age_min > age_max:
        raise LineAdsAPIError(400, f"age_min ({age_min}) ต้องน้อยกว่าหรือเท่ากับ age_max ({age_max})", "VALIDATION_ERROR")

    has_manual_targeting = bool(genders or interest_codes or interest_groups or behavior_codes or custom_audience_ids)
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

    advanced_targeting_groups = _build_advanced_targeting_groups(
        interest_codes=interest_codes,
        interest_groups=interest_groups,
        behavior_codes=behavior_codes,
    )
    if advanced_targeting_groups:
        targeting["includeAdvancedTargetings"] = advanced_targeting_groups

    return targeting


async def list_adsets(
    campaign_id: str | None = None,
    ad_account_id: str | None = None,
    status: str | None = None,
    fetch_all: bool = True,
    page: int = 1,
    size: int = 100,
) -> dict[str, Any]:
    try:
        if status is not None:
            require_one_of(status, ADSET_STATUS_FILTER, "status")
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        path = f"/adaccounts/{account_id}/adgroups"
        params: dict[str, Any] = {}
        if campaign_id is not None:
            params["campaignId"] = campaign_id
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


@track_change("adset")
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
    age_max: int | None = None,
    country: str = "TH",
    targeting_mode: str | None = None,
    genders: list[str] | None = None,
    interest_codes: list[str] | None = None,
    interest_groups: list[list[str]] | None = None,
    behavior_codes: list[str] | None = None,
    excluded_audience_ids: list[str] | None = None,
    custom_audience_ids: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    dry_run: bool = True,
    status: str = "PAUSED",
    workspace_dir: str | None = None,
) -> dict[str, Any]:
    """Create an adset with verified payload structure.

    Verified from real API:
    - autoBidType is required (FRIEND for CPF/GAIN_FRIENDS campaigns)
    - targeting is always required (flat object with targetingMode, ageMin, ageMax, country)
    - interest/behavior targeting must use targetingMode=MANUAL and includeAdvancedTargetings
    - use interest_groups for narrow targeting groups, e.g. [["4"], ["12"]]
    - GAIN_FRIENDS campaigns require excludedCustomAudienceIds (existing LINE OA friends audience)
    - bid_amount required only when bid_strategy=COST_CAP
    """
    try:
        require_one_of(status, {"PAUSED", "ACTIVE"}, "status")
        require_one_of(bid_type, BID_TYPES, "bid_type")
        require_one_of(bid_strategy, BID_STRATEGIES, "bid_strategy")
        require_one_of(auto_bid_type, AUTO_BID_TYPES, "auto_bid_type")
        if bid_strategy == "COST_CAP" and bid_amount is None:
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
            interest_groups=interest_groups,
            behavior_codes=behavior_codes,
            excluded_audience_ids=excluded_audience_ids,
            custom_audience_ids=custom_audience_ids,
        )

        payload = clean_dict({
            "campaignId": campaign_id,
            "name": name,
            "configuredStatus": status,
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
        return await write_entity(config, account_id, "adset", endpoint, payload)
    except Exception as error:
        return handle_tool_error(error)


@track_change("adset", "adset_id")
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
    interest_groups: list[list[str]] | None = None,
    behavior_codes: list[str] | None = None,
    excluded_audience_ids: list[str] | None = None,
    custom_audience_ids: list[str] | None = None,
    dry_run: bool = True,
    workspace_dir: str | None = None,
) -> dict[str, Any]:
    try:
        if status is not None:
            require_one_of(status, STATUSES, "status")
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        if targeting is None and any(
            value is not None
            for value in (
                age_min,
                age_max,
                targeting_mode,
                genders,
                interest_codes,
                interest_groups,
                behavior_codes,
                excluded_audience_ids,
                custom_audience_ids,
            )
        ):
            targeting = _build_targeting(
                age_min=age_min if age_min is not None else 20,
                age_max=age_max,
                country=country,
                targeting_mode=targeting_mode,
                genders=genders,
                interest_codes=interest_codes,
                interest_groups=interest_groups,
                behavior_codes=behavior_codes,
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
            return await preview_update(config, account_id, "adset", "update_adset", endpoint, payload, adset_id)
        return await write_entity(config, account_id, "adset", endpoint, payload, adset_id)
    except Exception as error:
        return handle_tool_error(error)


@track_change("adset", "adset_id")
async def pause_adset(
    adset_id: str,
    ad_account_id: str | None = None,
    dry_run: bool = True,
    workspace_dir: str | None = None,
) -> dict[str, Any]:
    return await update_adset(adset_id, ad_account_id, status="PAUSED", dry_run=dry_run, workspace_dir=workspace_dir)


@track_change("adset", "adset_id")
async def resume_adset(
    adset_id: str,
    ad_account_id: str | None = None,
    dry_run: bool = True,
    workspace_dir: str | None = None,
) -> dict[str, Any]:
    return await update_adset(adset_id, ad_account_id, status="ACTIVE", dry_run=dry_run, workspace_dir=workspace_dir)
