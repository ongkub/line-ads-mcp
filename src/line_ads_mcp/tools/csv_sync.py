"""Ad daily CSV sync tool for scheduled tasks."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
from typing import Any

from line_ads_mcp.client import LineAdsAPIError
from line_ads_mcp.tools.common import handle_tool_error, ok
from line_ads_mcp.tools.reports import get_report

CSV_HEADERS = [
    "date",
    "account_timezone",
    "campaign_id",
    "campaign_name",
    "objective",
    "adgroup_id",
    "adgroup_name",
    "ad_id",
    "ad_name",
    "impressions",
    "clicks",
    "spend",
    "currency",
    "results",
    "result_type",
    "pulled_at",
]

RUN_LOG_HEADERS = [
    "run_at",
    "date_range",
    "rows_written",
    "status",
    "note",
]


def _metric(row: dict[str, Any], *names: str) -> Any:
    stats = row.get("statistics") if isinstance(row.get("statistics"), dict) else {}
    for name in names:
        if name in row and row[name] is not None:
            return row[name]
        if name in stats and stats[name] is not None:
            return stats[name]
    return None


def _format_metric(val: Any) -> str:
    if val is None:
        return ""
    return str(val)


def _append_run_log(
    data_dir: Path,
    run_at: str,
    date_range: str,
    rows_written: int,
    status: str,
    note: str,
) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    log_file = data_dir / "run_log.csv"
    needs_header = not log_file.exists() or log_file.stat().st_size == 0
    with open(log_file, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        if needs_header:
            writer.writerow(RUN_LOG_HEADERS)
        writer.writerow([run_at, date_range, rows_written, status, note])


async def sync_ad_daily_csv(
    start_date: str,
    end_date: str,
    workspace_dir: str,
    ad_account_id: str | None = None,
    campaign_id: str | None = None,
    account_timezone: str | None = None,
    currency: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    try:
        if not workspace_dir or not str(workspace_dir).strip():
            raise LineAdsAPIError(400, "workspace_dir จำเป็นต้องระบุ", "VALIDATION_ERROR")

        ws_path = Path(workspace_dir)
        if not ws_path.is_absolute():
            raise LineAdsAPIError(400, f"workspace_dir ต้องเป็น absolute path ({workspace_dir})", "VALIDATION_ERROR")
        if not ws_path.is_dir():
            raise LineAdsAPIError(400, f"workspace_dir ไม่มีอยู่จริง ({workspace_dir})", "VALIDATION_ERROR")

        data_dir = ws_path / "line-ads-data"
        csv_file = data_dir / "ad_daily.csv"

        # Fetch report
        rep = await get_report(
            level="AD",
            start_date=start_date,
            end_date=end_date,
            ad_account_id=ad_account_id,
            campaign_id=campaign_id,
            by_day=True,
            fetch_all=True,
        )

        now_utc = datetime.now(timezone.utc).isoformat()
        date_range_str = f"{start_date}..{end_date}"

        if not rep.get("ok", True):
            if not dry_run:
                _append_run_log(
                    data_dir=data_dir,
                    run_at=now_utc,
                    date_range=date_range_str,
                    rows_written=0,
                    status="error",
                    note=rep.get("message", "report error"),
                )
            return rep

        rep_data = rep.get("data", {})
        report_rows = rep_data.get("data", [])
        if "date_range" in rep_data and isinstance(rep_data["date_range"], dict):
            s_dt = rep_data["date_range"].get("start")
            e_dt = rep_data["date_range"].get("end")
            if s_dt and e_dt:
                date_range_str = f"{s_dt}..{e_dt}"

        paging = rep_data.get("paging") if isinstance(rep_data.get("paging"), dict) else {}
        data_complete = bool(paging.get("complete", False))

        # Read existing CSV rows if present
        existing_rows: dict[tuple[str, str], dict[str, str]] = {}
        if csv_file.exists():
            with open(csv_file, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    d = r.get("date", "")
                    a = r.get("ad_id", "")
                    if d and a:
                        existing_rows[(d, a)] = r

        final_rows = dict(existing_rows)
        seen_keys_in_batch: set[tuple[str, str]] = set()
        inserted = 0
        replaced = 0
        unchanged = 0
        rejected = 0

        account_tz_str = str(account_timezone) if account_timezone is not None else ""
        currency_str = str(currency) if currency is not None else ""

        for row in report_rows:
            if not isinstance(row, dict):
                rejected += 1
                continue

            date_val = row.get("date")
            date_str = str(date_val).strip() if date_val is not None else ""

            campaign = row.get("campaign") if isinstance(row.get("campaign"), dict) else {}
            adgroup = row.get("adgroup") if isinstance(row.get("adgroup"), dict) else {}
            ad = row.get("ad") if isinstance(row.get("ad"), dict) else {}

            campaign_id_val = campaign.get("id") or row.get("campaignId") or row.get("campaign_id")
            campaign_id_str = str(campaign_id_val) if campaign_id_val is not None else ""

            campaign_name_val = campaign.get("name") or row.get("campaignName") or row.get("campaign_name")
            campaign_name_str = str(campaign_name_val) if campaign_name_val is not None else ""

            objective_val = (
                campaign.get("objective")
                or campaign.get("campaignObjective")
                or row.get("objective")
                or row.get("campaignObjective")
            )
            objective_str = str(objective_val) if objective_val is not None else ""

            adgroup_id_val = adgroup.get("id") or row.get("adgroupId") or row.get("adgroup_id")
            adgroup_id_str = str(adgroup_id_val) if adgroup_id_val is not None else ""

            adgroup_name_val = adgroup.get("name") or row.get("adgroupName") or row.get("adgroup_name")
            adgroup_name_str = str(adgroup_name_val) if adgroup_name_val is not None else ""

            ad_id_val = (
                ad.get("id")
                or row.get("adId")
                or row.get("ad_id")
                or (row.get("id") if not row.get("ad") else None)
            )
            ad_id_str = str(ad_id_val).strip() if ad_id_val is not None else ""

            ad_name_val = (
                ad.get("name")
                or row.get("adName")
                or row.get("ad_name")
                or (row.get("name") if not row.get("ad") else None)
            )
            ad_name_str = str(ad_name_val) if ad_name_val is not None else ""

            if not date_str or not ad_id_str:
                rejected += 1
                continue

            imp_val = _metric(row, "impressions", "imp")
            impressions_str = _format_metric(imp_val)

            click_val = _metric(row, "clicks", "click")
            clicks_str = _format_metric(click_val)

            spend_val = _metric(row, "spend", "cost")
            spend_str = _format_metric(spend_val)

            norm_obj = objective_str.strip().upper()
            if norm_obj == "GAIN_FRIENDS":
                if click_val is not None:
                    results_str = str(click_val)
                    result_type_str = "friends(click)"
                else:
                    results_str = ""
                    result_type_str = ""
            else:
                cv_val = _metric(row, "cv", "conversions")
                if cv_val is not None:
                    results_str = str(cv_val)
                    result_type_str = "cv"
                else:
                    results_str = ""
                    result_type_str = ""

            new_row: dict[str, str] = {
                "date": date_str,
                "account_timezone": account_tz_str,
                "campaign_id": campaign_id_str,
                "campaign_name": campaign_name_str,
                "objective": objective_str,
                "adgroup_id": adgroup_id_str,
                "adgroup_name": adgroup_name_str,
                "ad_id": ad_id_str,
                "ad_name": ad_name_str,
                "impressions": impressions_str,
                "clicks": clicks_str,
                "spend": spend_str,
                "currency": currency_str,
                "results": results_str,
                "result_type": result_type_str,
                "pulled_at": now_utc,
            }

            key = (date_str, ad_id_str)
            if key in seen_keys_in_batch:
                # Same key seen multiple times in this batch: update final_rows
                final_rows[key] = new_row
                continue

            seen_keys_in_batch.add(key)

            if key not in existing_rows:
                inserted += 1
                final_rows[key] = new_row
            else:
                old_row = existing_rows[key]
                is_different = any(
                    old_row.get(col, "") != new_row.get(col, "")
                    for col in CSV_HEADERS
                    if col != "pulled_at"
                )
                if is_different:
                    replaced += 1
                    final_rows[key] = new_row
                else:
                    unchanged += 1
                    final_rows[key] = old_row

        sorted_rows = sorted(final_rows.values(), key=lambda r: (r["date"], r["ad_id"]))
        rows_total = len(sorted_rows)
        preview = sorted_rows[:5]

        # Handling persistence
        if not dry_run:
            if not data_complete:
                # If report incomplete (paging.complete False) -> do not write ad_daily.csv;
                # still append run_log with status incomplete
                _append_run_log(
                    data_dir=data_dir,
                    run_at=now_utc,
                    date_range=date_range_str,
                    rows_written=0,
                    status="incomplete",
                    note=str(paging.get("reason") or "incomplete report"),
                )
            else:
                # Atomic write
                data_dir.mkdir(parents=True, exist_ok=True)
                temp_file = tempfile.NamedTemporaryFile(
                    dir=data_dir,
                    prefix="ad_daily_",
                    suffix=".tmp",
                    delete=False,
                    mode="w",
                    newline="",
                    encoding="utf-8",
                )
                temp_path = Path(temp_file.name)
                try:
                    with temp_file as f:
                        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS, lineterminator="\n")
                        writer.writeheader()
                        for r in sorted_rows:
                            writer.writerow(r)
                    os.replace(temp_path, csv_file)
                except Exception:
                    if temp_path.exists():
                        temp_path.unlink()
                    raise

                _append_run_log(
                    data_dir=data_dir,
                    run_at=now_utc,
                    date_range=date_range_str,
                    rows_written=rows_total,
                    status="ok",
                    note="",
                )

        return ok({
            "dry_run": dry_run,
            "csv_path": str(csv_file),
            "inserted": inserted,
            "replaced": replaced,
            "unchanged": unchanged,
            "rejected": rejected,
            "rows_total": rows_total,
            "data_complete": data_complete,
            "preview": preview,
        })

    except Exception as error:
        return handle_tool_error(error)
