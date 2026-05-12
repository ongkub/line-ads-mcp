"""Reporting tools."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from line_ads_mcp.client import LineAdsClient, LineAdsConfig, resolve_ad_account_id

from .common import handle_tool_error, ok, require_one_of

REPORT_LEVELS = {"CAMPAIGN", "ADGROUP", "AD"}
REPORT_LEVEL_PATH = {"CAMPAIGN": "campaign", "ADGROUP": "adgroup", "AD": "ad"}
DEFAULT_FIELDS = ["imp", "click", "cost", "ctr", "cpc", "cpm"]


def _date_yyyymmdd(days_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y%m%d")


def _api_date(value: str) -> str:
    """Accept YYYYMMDD or YYYY-MM-DD and return LINE API YYYY-MM-DD."""
    if len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return value


def _metric(row: dict[str, Any], *names: str) -> Any:
    stats = row.get("statistics") if isinstance(row.get("statistics"), dict) else {}
    for name in names:
        if name in row:
            return row.get(name)
        if name in stats:
            return stats.get(name)
    return 0


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_spend = sum(float(_metric(row, "spend", "cost") or 0) for row in rows)
    total_clicks = sum(int(_metric(row, "clicks", "click") or 0) for row in rows)
    total_impressions = sum(int(_metric(row, "impressions", "imp") or 0) for row in rows)
    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions else 0
    return {
        "total_spend": round(total_spend, 2),
        "total_clicks": total_clicks,
        "total_impressions": total_impressions,
        "avg_ctr": round(avg_ctr, 2),
    }


def _rows_from_response(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        for key in ("datas", "data", "reports", "items", "rows"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        return [data]
    if isinstance(data, list):
        return data
    return []


async def get_report(
    level: str,
    start_date: str,
    end_date: str,
    ad_account_id: str | None = None,
    campaign_id: str | None = None,
    fields: list[str] | None = None,
) -> dict[str, Any]:
    try:
        require_one_of(level, REPORT_LEVELS, "level")
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        params: dict[str, Any] = {
            "since": _api_date(start_date),
            "until": _api_date(end_date),
        }
        if fields:
            params["fields"] = ",".join(fields)
        if campaign_id:
            params["campaignId"] = campaign_id
        async with LineAdsClient(config) as client:
            raw = await client.get(f"/adaccounts/{account_id}/reports/online/{REPORT_LEVEL_PATH[level]}", params=params)
        rows = _rows_from_response(raw)
        return ok(
            {
                "report_level": level,
                "date_range": {"start": _api_date(start_date), "end": _api_date(end_date)},
                "data": rows,
                "summary": _summarize_rows(rows),
                "raw": raw,
            }
        )
    except Exception as error:
        return handle_tool_error(error)


async def get_daily_report(
    level: str = "CAMPAIGN",
    campaign_id: str | None = None,
    ad_account_id: str | None = None,
) -> dict[str, Any]:
    yesterday = _date_yyyymmdd(1)
    return await get_report(level, yesterday, yesterday, ad_account_id, campaign_id)


async def get_weekly_report(
    campaign_id: str | None = None,
    ad_account_id: str | None = None,
    level: str = "CAMPAIGN",
) -> dict[str, Any]:
    return await get_report(level, _date_yyyymmdd(7), _date_yyyymmdd(1), ad_account_id, campaign_id)

