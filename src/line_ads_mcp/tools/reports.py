"""Reporting tools."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient, LineAdsConfig, resolve_ad_account_id

from .common import handle_tool_error, ok, require_one_of
from .paging import MAX_PAGE_SIZE, fetch_all_pages

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


def _parse_date(value: str, param_name: str) -> datetime.date:
    formatted = _api_date(value)
    try:
        return datetime.strptime(formatted, "%Y-%m-%d").date()
    except Exception as exc:
        raise LineAdsAPIError(
            400,
            f"{param_name} รูปแบบวันที่ไม่ถูกต้อง ({value}) ต้องเป็น YYYY-MM-DD หรือ YYYYMMDD",
            "VALIDATION_ERROR",
        )


def _metric(row: dict[str, Any], *names: str) -> Any:
    stats = row.get("statistics") if isinstance(row.get("statistics"), dict) else {}
    for name in names:
        if name in row and row[name] is not None:
            return row[name]
        if name in stats and stats[name] is not None:
            return stats[name]
    return None


def _detect_metric_name(rows: list[dict[str, Any]], candidates: tuple[str, ...], default: str) -> str:
    for row in rows:
        stats = row.get("statistics") if isinstance(row.get("statistics"), dict) else {}
        for c in candidates:
            if c in row or c in stats:
                return c
    return default


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    spend_name = _detect_metric_name(rows, ("spend", "cost"), "spend")
    clicks_name = _detect_metric_name(rows, ("clicks", "click"), "clicks")
    imp_name = _detect_metric_name(rows, ("impressions", "imp"), "impressions")
    cv_name = _detect_metric_name(rows, ("cv", "conversions"), "cv")

    spend_vals: list[float] = []
    clicks_vals: list[int] = []
    imp_vals: list[int] = []
    cv_vals: list[int] = []
    missing_metrics: set[str] = set()

    for row in rows:
        s = _metric(row, "spend", "cost")
        if s is not None:
            spend_vals.append(float(s))
        else:
            missing_metrics.add(spend_name)

        c = _metric(row, "clicks", "click")
        if c is not None:
            clicks_vals.append(int(c))
        else:
            missing_metrics.add(clicks_name)

        i = _metric(row, "impressions", "imp")
        if i is not None:
            imp_vals.append(int(i))
        else:
            missing_metrics.add(imp_name)

        v = _metric(row, "cv", "conversions")
        if v is not None:
            cv_vals.append(int(v))
        else:
            missing_metrics.add(cv_name)

    total_spend = round(sum(spend_vals), 2)
    total_clicks = sum(clicks_vals)
    total_impressions = sum(imp_vals)
    total_cv = sum(cv_vals)

    avg_ctr = round(total_clicks / total_impressions * 100, 2) if total_impressions > 0 else None
    avg_cpc = round(total_spend / total_clicks, 2) if total_clicks > 0 else None
    avg_cpm = round(total_spend / total_impressions * 1000, 2) if total_impressions > 0 else None

    summary: dict[str, Any] = {
        "total_spend": total_spend,
        "total_clicks": total_clicks,
        "total_impressions": total_impressions,
        "total_cv": total_cv,
        "avg_ctr": avg_ctr,
        "avg_cpc": avg_cpc,
        "avg_cpm": avg_cpm,
    }
    if missing_metrics:
        summary["missing_metrics"] = sorted(missing_metrics)
    return summary


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
    adgroup_id: str | None = None,
    fetch_all: bool = True,
    page_size: int = 100,
    max_pages: int = 50,
    by_day: bool = False,
) -> dict[str, Any]:
    try:
        require_one_of(level, REPORT_LEVELS, "level")
        start_api = _api_date(start_date)
        end_api = _api_date(end_date)
        start_dt = _parse_date(start_date, "start_date")
        end_dt = _parse_date(end_date, "end_date")
        if end_dt < start_dt:
            raise LineAdsAPIError(
                400,
                f"end_date ({end_date}) ต้องไม่น้อยกว่า start_date ({start_date})",
                "VALIDATION_ERROR",
            )
        num_days = (end_dt - start_dt).days + 1
        if by_day and num_days > 93:
            raise LineAdsAPIError(
                400,
                f"by_day รองรับช่วงเวลาไม่เกิน 93 วัน (ระบุมา {num_days} วัน)",
                "VALIDATION_ERROR",
            )

        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        path = f"/adaccounts/{account_id}/reports/online/{REPORT_LEVEL_PATH[level]}"

        base_params: dict[str, Any] = {}
        if fields:
            base_params["fields"] = ",".join(fields)
        if campaign_id:
            base_params["campaignId"] = campaign_id
        if adgroup_id:
            base_params["adgroupId"] = adgroup_id

        raw_data: Any = None

        if by_day:
            all_rows: list[dict[str, Any]] = []
            days_paging: list[dict[str, Any]] = []
            async with LineAdsClient(config) as client:
                curr = start_dt
                while curr <= end_dt:
                    day_str = curr.strftime("%Y-%m-%d")
                    day_params = {**base_params, "since": day_str, "until": day_str}
                    if fetch_all:
                        paged = await fetch_all_pages(
                            client,
                            path,
                            params=day_params,
                            page_size=page_size,
                            max_pages=max_pages,
                        )
                        day_rows = paged["datas"]
                        p_info = paged["paging"]
                    else:
                        size = max(1, min(int(page_size), MAX_PAGE_SIZE))
                        raw_day = await client.get(path, params={**day_params, "page": 1, "size": size})
                        day_rows = _rows_from_response(raw_day)
                        p_meta = raw_day.get("paging") if isinstance(raw_day, dict) else None
                        tot = (
                            p_meta.get("totalElements")
                            if isinstance(p_meta, dict) and isinstance(p_meta.get("totalElements"), int)
                            else None
                        )
                        comp = (len(day_rows) >= tot) if tot is not None else None
                        p_info = {
                            "pages_fetched": 1,
                            "total_elements": tot,
                            "rows": len(day_rows),
                            "complete": comp,
                            "reason": None,
                        }

                    for row in day_rows:
                        if isinstance(row, dict):
                            row["date"] = day_str
                    all_rows.extend(day_rows)
                    days_paging.append({"date": day_str, **p_info})
                    curr += timedelta(days=1)

            tot_pages = sum(d["pages_fetched"] for d in days_paging)
            all_totals = [d["total_elements"] for d in days_paging]
            overall_total = sum(all_totals) if all(t is not None for t in all_totals) else None
            overall_complete = all(d.get("complete") is True for d in days_paging)
            overall_reason = next((d.get("reason") for d in days_paging if d.get("reason")), None)

            paging_result = {
                "pages_fetched": tot_pages,
                "total_elements": overall_total,
                "rows": len(all_rows),
                "complete": overall_complete,
                "reason": overall_reason,
                "days": days_paging,
                "per_day": days_paging,
            }
            rows = all_rows
        elif fetch_all:
            params = {**base_params, "since": start_api, "until": end_api}
            async with LineAdsClient(config) as client:
                paged = await fetch_all_pages(
                    client,
                    path,
                    params=params,
                    page_size=page_size,
                    max_pages=max_pages,
                )
            rows = paged["datas"]
            paging_result = paged["paging"]
        else:
            size = max(1, min(int(page_size), MAX_PAGE_SIZE))
            params = {**base_params, "since": start_api, "until": end_api, "page": 1, "size": size}
            async with LineAdsClient(config) as client:
                raw_data = await client.get(path, params=params)
            rows = _rows_from_response(raw_data)
            p_meta = raw_data.get("paging") if isinstance(raw_data, dict) else None
            tot = (
                p_meta.get("totalElements")
                if isinstance(p_meta, dict) and isinstance(p_meta.get("totalElements"), int)
                else None
            )
            comp = (len(rows) >= tot) if tot is not None else None
            paging_result = {
                "pages_fetched": 1,
                "total_elements": tot,
                "rows": len(rows),
                "complete": comp,
                "reason": None,
            }

        result: dict[str, Any] = {
            "report_level": level,
            "date_range": {"start": start_api, "end": end_api},
            "data": rows,
            "summary": _summarize_rows(rows),
            "paging": paging_result,
            "date_basis": "UTC",
            "by_day": by_day,
        }
        if not fetch_all and not by_day and raw_data is not None:
            result["raw"] = raw_data

        return ok(result)
    except Exception as error:
        return handle_tool_error(error)


async def get_daily_report(
    level: str = "AD",
    campaign_id: str | None = None,
    ad_account_id: str | None = None,
    fetch_all: bool = True,
) -> dict[str, Any]:
    yesterday = _date_yyyymmdd(1)
    return await get_report(
        level=level,
        start_date=yesterday,
        end_date=yesterday,
        ad_account_id=ad_account_id,
        campaign_id=campaign_id,
        fetch_all=fetch_all,
        by_day=True,
    )


async def get_weekly_report(
    level: str = "CAMPAIGN",
    campaign_id: str | None = None,
    ad_account_id: str | None = None,
    fetch_all: bool = True,
    by_day: bool = False,
) -> dict[str, Any]:
    return await get_report(
        level=level,
        start_date=_date_yyyymmdd(7),
        end_date=_date_yyyymmdd(1),
        ad_account_id=ad_account_id,
        campaign_id=campaign_id,
        fetch_all=fetch_all,
        by_day=by_day,
    )
