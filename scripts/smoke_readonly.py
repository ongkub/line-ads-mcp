#!/usr/bin/env python3
"""Smoke test script for LINE Ads MCP — READ-ONLY verification against a real account.

Runs read-only queries (list campaigns, ad sets, ads, 7-day report, inspect first entity,
and optional ARS reach simulation) and prints a compact Thai summary.
Never calls any write tools.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys

# Ensure src/ is on sys.path even when run directly without PYTHONPATH=src
_src_dir = str(Path(__file__).resolve().parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from dotenv import load_dotenv

# Assert safety: ONLY import read tools, never write tools
from line_ads_mcp.tools.ads import list_ads
from line_ads_mcp.tools.adsets import list_adsets
from line_ads_mcp.tools.campaigns import list_campaigns
from line_ads_mcp.tools.entities import get_entity
from line_ads_mcp.tools.reach import estimate_adset_reach
from line_ads_mcp.tools.reports import get_report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ตรวจสอบการเชื่อมต่อ LINE Ads API แบบอ่านอย่างเดียว (Read-only smoke test)",
    )
    parser.add_argument(
        "--reach",
        metavar="CAMPAIGN_ID",
        help="Campaign ID สำหรับทดสอบประมาณการ reach (ARS simulation)",
    )
    parser.add_argument(
        "--budget",
        type=float,
        metavar="THB",
        help="งบประมาณต่อวัน (THB) สำหรับทดสอบประมาณการ reach",
    )
    parser.add_argument(
        "--ad-account-id",
        metavar="ACCOUNT_ID",
        help="LINE Ads Account ID (หากไม่ระบุจะใช้ค่าจาก LINE_ADS_AD_ACCOUNT_ID ใน .env)",
    )
    return parser.parse_args(argv)


async def run_smoke(args: argparse.Namespace) -> int:
    load_dotenv()
    account_id = args.ad_account_id

    print("=== เริ่มการตรวจสอบ LINE Ads API (Read-Only Smoke Test) ===")

    # 1. list_campaigns
    print("\n[1/5] ตรวจสอบรายการ Campaigns ทั้งบัญชี...")
    c_res = await list_campaigns(ad_account_id=account_id, fetch_all=True)
    if not c_res.get("ok"):
        print(f"❌ list_campaigns ล้มเหลว: {c_res.get('message')}")
        return 1
    c_data = c_res.get("data", {})
    campaigns = c_data.get("datas", [])
    c_paging = c_data.get("paging", {})
    print(f"  ✓ พบ {len(campaigns)} แคมเปญ (paging.complete: {c_paging.get('complete', True)})")

    # 2. list_adsets (whole account)
    print("\n[2/5] ตรวจสอบรายการ Ad Sets ทั้งบัญชี...")
    ag_res = await list_adsets(campaign_id=None, ad_account_id=account_id, fetch_all=True)
    if not ag_res.get("ok"):
        print(f"❌ list_adsets ล้มเหลว: {ag_res.get('message')}")
        return 1
    ag_data = ag_res.get("data", {})
    adsets = ag_data.get("datas", [])
    ag_paging = ag_data.get("paging", {})
    print(f"  ✓ พบ {len(adsets)} ชุดโฆษณา (paging.complete: {ag_paging.get('complete', True)})")

    # 3. list_ads
    print("\n[3/5] ตรวจสอบรายการ Ads ทั้งบัญชี...")
    ad_res = await list_ads(ad_account_id=account_id, fetch_all=True)
    if not ad_res.get("ok"):
        print(f"❌ list_ads ล้มเหลว: {ad_res.get('message')}")
        return 1
    ad_data = ad_res.get("data", {})
    ads = ad_data.get("datas", [])
    ad_paging = ad_data.get("paging", {})
    print(f"  ✓ พบ {len(ads)} โฆษณา (paging.complete: {ad_paging.get('complete', True)})")

    # 4. get_report (level CAMPAIGN, last 7 days, fetch_all)
    now = datetime.now(timezone.utc)
    end_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    print(f"\n[4/5] ดึงรายงานระดับ Campaign ย้อนหลัง 7 วัน ({start_date} ถึง {end_date})...")
    rep_res = await get_report(
        level="CAMPAIGN",
        start_date=start_date,
        end_date=end_date,
        ad_account_id=account_id,
        fetch_all=True,
    )
    if not rep_res.get("ok"):
        print(f"❌ get_report ล้มเหลว: {rep_res.get('message')}")
        return 1
    rep_data = rep_res.get("data", {})
    rep_rows = rep_data.get("data", [])
    rep_paging = rep_data.get("paging", {})
    rep_summary = rep_data.get("summary", {})
    total_spend = rep_summary.get("total_spend", 0)
    print(f"  ✓ ข้อมูลรายงาน: {len(rep_rows)} แถว")
    print(f"  ✓ paging.complete: {rep_paging.get('complete')}")
    print(f"  ✓ ยอดใช้จ่ายรวม: ฿{total_spend:,.2f}" if total_spend is not None else "  ✓ ยอดใช้จ่ายรวม: ฿0.00")

    # 5. get_entity on first campaign
    print("\n[5/5] ตรวจสอบ Entity แคมเปญแรก...")
    if campaigns:
        first_id = str(campaigns[0].get("id"))
        ent_res = await get_entity("campaign", first_id, ad_account_id=account_id)
        if not ent_res.get("ok"):
            print(f"  ⚠️ get_entity ล้มเหลว: {ent_res.get('message')}")
        else:
            ent = ent_res.get("data", {})
            print(f"  ✓ Campaign ID: {first_id}")
            print(f"  ✓ ชื่อ: {ent.get('name')}")
            print(f"  ✓ configuredStatus: {ent.get('configured_status')}")
            print(f"  ✓ deliveryStatus: {ent.get('delivery_status')}")
    else:
        print("  — บัญชีนี้ยังไม่มีแคมเปญให้ตรวจสอบ entity")

    # Optional Reach Simulation (ARS)
    if args.reach and args.budget:
        print(f"\n[ARS Simulation] ประมาณการ Reach สำหรับ Campaign ID {args.reach} (งบ ฿{args.budget:,.2f}/วัน)...")
        # Inspect campaign objective to select suitable bid parameters
        camp_ent = await get_entity("campaign", args.reach, ad_account_id=account_id)
        raw_camp = camp_ent.get("data", {}).get("raw", {}) if camp_ent.get("ok") else {}
        obj = raw_camp.get("campaignObjective") or "WEBSITE_TRAFFIC"

        if obj == "GAIN_FRIENDS":
            bid_type = "CPF"
            auto_bid_type = "FRIEND"
        elif obj == "REACH":
            bid_type = "CPM"
            auto_bid_type = "REACH"
        elif obj == "VIDEO_VIEW":
            bid_type = "CPM"
            auto_bid_type = "VIDEO_VIEW"
        elif obj == "APP_INSTALL":
            bid_type = "CPC"
            auto_bid_type = "INSTALL"
        else:
            bid_type = "CPC"
            auto_bid_type = "CLICK"

        reach_res = await estimate_adset_reach(
            campaign_id=str(args.reach),
            campaign_objective=obj,
            daily_budget=float(args.budget),
            bid_type=bid_type,
            auto_bid_type=auto_bid_type,
            ad_account_id=account_id,
        )
        if not reach_res.get("ok"):
            print(f"  ❌ estimate_adset_reach ล้มเหลว: {reach_res.get('message')}")
        else:
            rdata = reach_res.get("data", {})
            reach_range = rdata.get("reach", {})
            clicks_range = rdata.get("clicks", {})
            print(f"  ✓ Objective: {obj} (bid: {bid_type}/{auto_bid_type})")
            print(f"  ✓ Reach โดยประมาณ: {reach_range.get('min', 0):,} - {reach_range.get('max', 0):,} คน")
            print(f"  ✓ ผลลัพธ์/คลิกโดยประมาณ: {clicks_range.get('min', 0):,} - {clicks_range.get('max', 0):,} ครั้ง")
            print(f"  ✓ หมายเหตุ: {rdata.get('note')}")

    print("\n=== การตรวจสอบเสร็จสมบูรณ์เรียบร้อย (Read-Only) ===")
    return 0


def main() -> None:
    args = parse_args()
    code = asyncio.run(run_smoke(args))
    sys.exit(code)


if __name__ == "__main__":
    main()
