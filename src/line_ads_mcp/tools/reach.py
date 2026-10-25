"""Reach and ARS (Adgroup Result Simulator) simulation tools."""

from __future__ import annotations

from typing import Any

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient, LineAdsConfig, resolve_ad_account_id

from .adsets import (
    AUTO_BID_TYPES,
    BID_STRATEGIES,
    _build_targeting,
)
from .campaigns import OBJECTIVES, normalize_objective
from .common import clean_dict, handle_tool_error, ok, require_one_of, to_micro

NOTE_ARS = "ค่าประมาณจาก LINE Ads Adgroup Result Simulator ไม่ใช่ขนาดกลุ่มที่การันตี"

# API v3.12.3 ARS simulation allowed bid types: CPC, CPF, CPM
ARS_BID_TYPES = {"CPC", "CPF", "CPM"}


async def estimate_adset_reach(
    campaign_id: str,
    campaign_objective: str,
    daily_budget: float,
    bid_type: str,
    auto_bid_type: str,
    ad_account_id: str | None = None,
    adset_id: str | None = None,
    bid_amount: float | None = None,
    bid_strategy: str | None = None,
    targeting: dict[str, Any] | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    genders: list[str] | None = None,
    interest_codes: list[str] | None = None,
    custom_audience_ids: list[str] | None = None,
    excluded_audience_ids: list[str] | None = None,
    country: str = "TH",
) -> dict[str, Any]:
    """Estimate adset reach and clicks via LINE Ads ARS (Adgroup Result Simulator).

    This is a read-only simulation: creates nothing on LINE Ads, and does not accept dry_run.
    POSTs to /adaccounts/{id}/simulation/ars with camelCase parameters.
    """
    try:
        campaign_objective = normalize_objective(campaign_objective)
        require_one_of(campaign_objective, OBJECTIVES, "campaign_objective")
        require_one_of(bid_type, ARS_BID_TYPES, "bid_type")
        require_one_of(auto_bid_type, AUTO_BID_TYPES, "auto_bid_type")
        if bid_strategy is not None:
            require_one_of(bid_strategy, BID_STRATEGIES, "bid_strategy")

        if bid_amount is None and bid_strategy != "LOWEST_COST":
            raise LineAdsAPIError(
                400,
                'ต้องระบุ bid_amount เมื่อ bid_strategy เป็น COST_CAP หรือไม่ระบุ หรือใช้ bid_strategy="LOWEST_COST"',
                "VALIDATION_ERROR",
            )

        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)

        adjusted = []
        if targeting is None:
            effective_age_min = 20 if age_min is None else age_min
            targeting_payload = _build_targeting(
                age_min=effective_age_min,
                age_max=age_max,
                country=country,
                targeting_mode="MANUAL",
                genders=genders,
                interest_codes=interest_codes,
                excluded_audience_ids=excluded_audience_ids,
                custom_audience_ids=custom_audience_ids,
            )
        else:
            targeting_payload = dict(targeting)
            if targeting_payload.get("targetingMode") != "MANUAL":
                targeting_payload["targetingMode"] = "MANUAL"
                adjusted.append("targetingMode AUTO→MANUAL (ARS รับเฉพาะ MANUAL)")

        body = clean_dict(
            {
                "adaccountId": account_id,
                "campaignId": campaign_id,
                "adgroupId": adset_id,
                "campaignObjective": campaign_objective,
                "dailyBudgetMicro": to_micro(daily_budget),
                "bidAmountMicro": to_micro(bid_amount) if bid_amount is not None else None,
                "bidType": bid_type,
                "bidStrategy": bid_strategy,
                "autoBidType": auto_bid_type,
                "targeting": targeting_payload,
            }
        )

        endpoint = f"/adaccounts/{account_id}/simulation/ars"

        async with LineAdsClient(config) as client:
            resp = await client.post(endpoint, body)

        raw_reach = resp.get("reach")
        if isinstance(raw_reach, list) and len(raw_reach) == 2:
            reach_dict: dict[str, Any] | None = {"min": raw_reach[0], "max": raw_reach[1]}
        elif isinstance(raw_reach, dict):
            reach_dict = raw_reach
        else:
            reach_dict = None

        raw_clicks = resp.get("result")
        if isinstance(raw_clicks, list) and len(raw_clicks) == 2:
            clicks_dict: dict[str, Any] | None = {"min": raw_clicks[0], "max": raw_clicks[1]}
        elif isinstance(raw_clicks, dict):
            clicks_dict = raw_clicks
        else:
            clicks_dict = None

        absent_fields = resp.get("absentFields")
        invalid_fields = resp.get("invalidFields")
        ignored_fields = resp.get("ignoredFields")

        return ok(
            {
                "reach": reach_dict,
                "clicks": clicks_dict,
                "absent_fields": absent_fields,
                "invalid_fields": invalid_fields,
                "ignored_fields": ignored_fields,
                "request": body,
                "note": NOTE_ARS,
                **({"adjusted": adjusted} if adjusted else {}),
            }
        )
    except Exception as error:
        return handle_tool_error(error)
