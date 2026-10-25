"""Read-only spend cap checks; these never pause or modify campaigns."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from line_ads_mcp.client import LineAdsAPIError

from .common import handle_tool_error, ok
from .reports import _metric, _parse_date, get_report


def _money(value: Any) -> Decimal:
    """Normalize report float noise to THB satang before money decisions."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def check_spend_cap(
    cap_amount: float,
    start_date: str,
    end_date: str,
    campaign_id: str | None = None,
    ad_account_id: str | None = None,
    period_end: str | None = None,
) -> dict[str, Any]:
    """Check reported spend against a THB cap, optionally estimating period spend.

    Projection is a linear estimate, including when only partial data is available;
    consult data_complete before relying on it. Dates use the report's UTC basis.
    """
    try:
        try:
            cap = Decimal(str(cap_amount))
        except (InvalidOperation, ValueError):
            cap = Decimal("NaN")
        if not cap.is_finite() or cap <= 0:
            raise LineAdsAPIError(400, "cap_amount ต้องเป็นจำนวนบาทที่มากกว่า 0", "VALIDATION_ERROR")

        start = _parse_date(start_date, "start_date")
        end = _parse_date(end_date, "end_date")
        if end < start:
            raise LineAdsAPIError(400, "end_date ต้องไม่น้อยกว่า start_date", "VALIDATION_ERROR")
        period = None
        if period_end is not None:
            try:
                period = date.fromisoformat(period_end)
                if period.isoformat() != period_end or period < end:
                    raise ValueError
            except (TypeError, ValueError):
                raise LineAdsAPIError(
                    400, "period_end ต้องเป็น YYYY-MM-DD และไม่น้อยกว่า end_date", "VALIDATION_ERROR"
                )

        report = await get_report(
            level="CAMPAIGN",
            start_date=start_date,
            end_date=end_date,
            campaign_id=campaign_id,
            ad_account_id=ad_account_id,
            fetch_all=True,
        )
        if not report.get("ok"):
            return report

        data = report["data"]
        spend = _money(data["summary"]["total_spend"])
        paging = data.get("paging") or {}
        complete = paging.get("complete") is True
        # A row without cost means spend may be understated: only "exceeded" can still be proven.
        missing_cost = bool({"spend", "cost"} & set(data["summary"].get("missing_metrics") or []))
        complete = complete and not missing_cost
        status = "exceeded" if spend > cap else "within_cap" if complete else "indeterminate"
        per_campaign = []
        for row in data["data"]:
            cost = _metric(row, "spend", "cost")
            nested = row.get("campaign") if isinstance(row.get("campaign"), dict) else {}
            per_campaign.append({
                "campaign_id": nested.get("id", row.get("campaignId", row.get("campaign_id", row.get("id", campaign_id)))),
                "name": nested.get("name", row.get("campaignName", row.get("name"))),
                "spend": float(_money(cost)) if cost is not None else None,
            })

        result: dict[str, Any] = {
            "status": status,
            "spend": float(spend),
            "cap": float(cap),
            "difference": float(_money(spend - cap)),
            "percent_of_cap": float(_money(spend / cap * 100)),
            "date_range": {"start": start.isoformat(), "end": end.isoformat()},
            "campaign_id": campaign_id,
            "data_complete": complete,
            "per_campaign": per_campaign,
            "cost_unit_note": "ค่า cost จากรายงาน LINE Ads เป็นบาท (THB) — ตรวจกับงบรายวันของบัญชีจริง 25 ต.ค. 2026",
            "date_basis": "UTC",
        }
        if missing_cost:
            result["reason"] = "บางแถวในรายงานไม่มีค่า cost จึงยืนยันว่ายังไม่เกินเพดานไม่ได้"
        elif not complete:
            result["reason"] = paging.get("reason") or "ไม่สามารถยืนยันว่าได้รับข้อมูลรายงานครบทุกหน้า"
        if period is not None:
            days_elapsed = (end - start).days + 1
            days_total = (period - start).days + 1
            projected = _money(spend / days_elapsed * days_total)
            result["projection"] = {
                "projected_spend": float(projected),
                "projected_status": "exceeded" if projected > cap else "within_cap",
                "formula": "spend ÷ วันที่ผ่านไป × วันทั้งงวด",
                "is_estimate": True,
                "note": "ค่าประมาณจากอัตราการใช้จ่ายเฉลี่ยของข้อมูลที่ได้รับ ไม่ใช่ยอดใช้จ่ายจริง",
            }
        return ok(result)
    except Exception as error:
        return handle_tool_error(error)
