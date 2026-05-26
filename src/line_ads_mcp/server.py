"""MCP server entry point for LINE Ads tools."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from line_ads_mcp.tools.ads import create_ad, get_ad_status, list_ads, upload_media
from line_ads_mcp.tools.adsets import create_adset, list_adsets, pause_adset, resume_adset, update_adset
from line_ads_mcp.tools.audiences import create_audience, list_audiences
from line_ads_mcp.tools.campaigns import (
    create_campaign,
    list_campaigns,
    pause_campaign,
    resume_campaign,
    update_campaign,
)
from line_ads_mcp.tools.codes import list_advanced_targeting_codes
from line_ads_mcp.tools.reports import get_daily_report, get_report, get_weekly_report

ToolFn = Callable[..., Awaitable[dict[str, Any]]]

server = Server("line-ads")


def schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


TOOLS: dict[str, tuple[str, dict[str, Any], ToolFn]] = {
    "list_campaigns": (
        "ดึงรายการ campaigns ทั้งหมดใน ad account",
        schema(
            {
                "ad_account_id": {"type": "string"},
                "page": {"type": "integer", "default": 1},
                "size": {"type": "integer", "default": 20, "maximum": 500},
            }
        ),
        list_campaigns,
    ),
    "create_campaign": (
        "สร้าง campaign ใหม่แบบ dry_run เป็นค่าเริ่มต้นเพื่อความปลอดภัย",
        schema(
            {
                "name": {"type": "string"},
                "objective": {
                    "type": "string",
                    "enum": [
                        "GAIN_FRIENDS",
                        "WEBSITE_TRAFFIC",
                        "CONVERSIONS",
                        "REACH",
                        "APP_INSTALL",
                        "VIDEO_VIEW",
                    ],
                },
                "ad_account_id": {"type": "string"},
                "daily_budget": {"type": "number", "description": "งบประมาณต่อวัน หน่วย THB (จะแปลงเป็น micro อัตโนมัติ)"},
                "total_budget": {"type": "number", "description": "งบประมาณรวม หน่วย THB (จะแปลงเป็น micro อัตโนมัติ)"},
                "start_date": {"type": "string", "description": "วันเวลาเริ่ม campaign แบบ ISO เช่น 2026-05-14T09:00:00+07:00 (required by LINE Ads API)"},
                "end_date": {"type": "string"},
                "dry_run": {"type": "boolean", "default": True},
            },
            ["name", "objective", "start_date"],
        ),
        create_campaign,
    ),
    "update_campaign": (
        "แก้ไข campaign เช่น budget/status/name แบบ dry_run เป็นค่าเริ่มต้น",
        schema(
            {
                "campaign_id": {"type": "string"},
                "ad_account_id": {"type": "string"},
                "status": {"type": "string", "enum": ["ACTIVE", "PAUSED"]},
                "daily_budget": {"type": "number"},
                "name": {"type": "string"},
                "dry_run": {"type": "boolean", "default": True},
            },
            ["campaign_id"],
        ),
        update_campaign,
    ),
    "pause_campaign": (
        "หยุด campaign ชั่วคราว แบบ dry_run เป็นค่าเริ่มต้น",
        schema({"campaign_id": {"type": "string"}, "ad_account_id": {"type": "string"}, "dry_run": {"type": "boolean", "default": True}}, ["campaign_id"]),
        pause_campaign,
    ),
    "resume_campaign": (
        "เปิด campaign กลับมาทำงาน แบบ dry_run เป็นค่าเริ่มต้น",
        schema({"campaign_id": {"type": "string"}, "ad_account_id": {"type": "string"}, "dry_run": {"type": "boolean", "default": True}}, ["campaign_id"]),
        resume_campaign,
    ),
    "list_adsets": (
        "ดึงรายการ ad sets/adgroups ใน campaign",
        schema({"campaign_id": {"type": "string"}, "ad_account_id": {"type": "string"}}, ["campaign_id"]),
        list_adsets,
    ),
    "create_adset": (
        "สร้าง ad set/adgroup ใหม่ แบบ dry_run เป็นค่าเริ่มต้น",
        schema(
            {
                "campaign_id": {"type": "string"},
                "name": {"type": "string"},
                "bid_type": {"type": "string", "enum": ["CPF", "CPM", "CPC", "CPV"], "description": "CPF สำหรับ GAIN_FRIENDS"},
                "bid_strategy": {"type": "string", "enum": ["COST_CAP", "LOWEST_COST"], "description": "COST_CAP ต้องระบุ bid_amount ด้วย"},
                "auto_bid_type": {"type": "string", "enum": ["FRIEND", "CLICK", "INSTALL", "VIDEO_VIEW", "REACH"], "description": "FRIEND สำหรับ GAIN_FRIENDS+CPF"},
                "daily_budget": {"type": "number", "description": "งบต่อวัน หน่วย THB (required)"},
                "ad_account_id": {"type": "string"},
                "bid_amount": {"type": "number", "description": "ราคา bid สูงสุด หน่วย THB (required เมื่อ bid_strategy=COST_CAP)"},
                "age_min": {"type": "integer", "default": 20, "description": "อายุต่ำสุด (ค่าที่ valid: 20, 25, 30, 35, 40, 45, 55, 65 เท่านั้น — ค่าอื่น API reject)"},
                "age_max": {"type": "integer", "default": 65, "description": "อายุสูงสุด"},
                "country": {"type": "string", "default": "TH"},
                "targeting_mode": {"type": "string", "enum": ["AUTO", "MANUAL"], "description": "ถ้ามี interest_codes ให้ใช้ MANUAL; tool จะเลือกให้เองถ้าไม่ระบุ"},
                "genders": {"type": "array", "items": {"type": "string"}},
                "interest_codes": {"type": "array", "items": {"type": "string"}, "description": "ใช้ code จาก list_advanced_targeting_codes เช่น อาชีพและธุรกิจ=4"},
                "interest_groups": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}, "description": "ใช้ทำ narrow targeting เช่น [[\"4\"], [\"12\"]]"},
                "behavior_codes": {"type": "array", "items": {"type": "string"}, "description": "ใช้ code จาก list_advanced_targeting_codes เช่น มีกำลังการซื้อสูง=1590"},
                "excluded_audience_ids": {"type": "array", "items": {"type": "string"}, "description": "GAIN_FRIENDS campaigns ต้องใส่ audience ID ของเพื่อนปัจจุบัน (ดูจาก list_audiences)"},
                "custom_audience_ids": {"type": "array", "items": {"type": "string"}},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "dry_run": {"type": "boolean", "default": True},
            },
            ["campaign_id", "name", "bid_type", "bid_strategy", "auto_bid_type", "daily_budget"],
        ),
        create_adset,
    ),
    "update_adset": (
        "แก้ไข ad set/adgroup แบบ dry_run เป็นค่าเริ่มต้น",
        schema(
            {
                "adset_id": {"type": "string"},
                "ad_account_id": {"type": "string"},
                "status": {"type": "string", "enum": ["ACTIVE", "PAUSED"]},
                "daily_budget": {"type": "number", "description": "งบประมาณต่อวัน หน่วย THB"},
                "bid_amount": {"type": "number", "description": "ราคา bid สูงสุด หน่วย THB"},
                "targeting": {"type": "object"},
                "age_min": {"type": "integer"},
                "age_max": {"type": "integer"},
                "country": {"type": "string", "default": "TH"},
                "targeting_mode": {"type": "string", "enum": ["AUTO", "MANUAL"]},
                "genders": {"type": "array", "items": {"type": "string"}},
                "interest_codes": {"type": "array", "items": {"type": "string"}},
                "interest_groups": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
                "behavior_codes": {"type": "array", "items": {"type": "string"}},
                "excluded_audience_ids": {"type": "array", "items": {"type": "string"}},
                "custom_audience_ids": {"type": "array", "items": {"type": "string"}},
                "dry_run": {"type": "boolean", "default": True},
            },
            ["adset_id"],
        ),
        update_adset,
    ),
    "pause_adset": (
        "หยุด ad set ชั่วคราว แบบ dry_run เป็นค่าเริ่มต้น",
        schema({"adset_id": {"type": "string"}, "ad_account_id": {"type": "string"}, "dry_run": {"type": "boolean", "default": True}}, ["adset_id"]),
        pause_adset,
    ),
    "resume_adset": (
        "เปิด ad set กลับมาทำงาน แบบ dry_run เป็นค่าเริ่มต้น",
        schema({"adset_id": {"type": "string"}, "ad_account_id": {"type": "string"}, "dry_run": {"type": "boolean", "default": True}}, ["adset_id"]),
        resume_adset,
    ),
    "upload_media": (
        "อัปโหลดรูปหรือวิดีโอเพื่อใช้สร้าง ad แบบ dry_run เป็นค่าเริ่มต้น",
        schema({"file_path": {"type": "string"}, "ad_account_id": {"type": "string"}, "dry_run": {"type": "boolean", "default": True}}, ["file_path"]),
        upload_media,
    ),
    "create_ad": (
        "สร้าง ad ใหม่ แบบ dry_run เป็นค่าเริ่มต้น — ต้องมี imageHash จาก upload_media ก่อน",
        schema(
            {
                "adset_id": {"type": "string"},
                "name": {"type": "string"},
                "image_hash": {"type": "string", "description": "imageHash ที่ได้จาก upload_media (ไม่ใช่ media_id)"},
                "title": {"type": "string", "description": "ข้อความหัวโฆษณา (สูงสุด ~25 ตัวอักษร)"},
                "call_to_action": {
                    "type": "string",
                    "enum": ["ADD_FRIEND", "LEARN_MORE", "SHOP_NOW", "SIGN_UP", "CONTACT_US", "DOWNLOAD"],
                    "description": "ADD_FRIEND สำหรับ GAIN_FRIENDS campaign",
                },
                "ad_account_id": {"type": "string"},
                "campaign_id": {"type": "string", "description": "campaign ID (แนะนำให้ส่งเสมอตาม LINE Ads API spec)"},
                "creative_format": {"type": "string", "enum": ["IMAGE", "VIDEO"], "default": "IMAGE"},
                "description": {"type": "string"},
                "long_title": {"type": "string", "description": "หัวข้อยาว — บังคับเมื่อใช้ small_image_hash (รูปเล็ก 600×400px)"},
                "destination_url": {"type": "string", "description": "URL สำหรับ WEBSITE_TRAFFIC campaigns เท่านั้น"},
                "small_image_hash": {"type": "string", "description": "imageHash ของรูปขนาดเล็ก 600×400px (แนะนำให้ใส่เสมอเพื่อเพิ่ม placement coverage)"},
                "dry_run": {"type": "boolean", "default": True},
            },
            ["adset_id", "name", "image_hash", "title", "call_to_action"],
        ),
        create_ad,
    ),
    "get_ad_status": (
        "ตรวจสอบสถานะ review/approved/rejected ของ ad",
        schema({"ad_id": {"type": "string"}, "ad_account_id": {"type": "string"}}, ["ad_id"]),
        get_ad_status,
    ),
    "list_ads": (
        "ดึงรายการ ads ใน ad set/adgroup",
        schema({"adset_id": {"type": "string"}, "ad_account_id": {"type": "string"}}, ["adset_id"]),
        list_ads,
    ),
    "get_report": (
        "ดึง performance report ตาม level และช่วงวันที่",
        schema(
            {
                "level": {"type": "string", "enum": ["CAMPAIGN", "ADGROUP", "AD"]},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "ad_account_id": {"type": "string"},
                "campaign_id": {"type": "string"},
                "fields": {"type": "array", "items": {"type": "string"}},
            },
            ["level", "start_date", "end_date"],
        ),
        get_report,
    ),
    "get_daily_report": (
        "shortcut ดึง report เมื่อวาน",
        schema({"level": {"type": "string", "default": "CAMPAIGN"}, "campaign_id": {"type": "string"}, "ad_account_id": {"type": "string"}}),
        get_daily_report,
    ),
    "get_weekly_report": (
        "shortcut ดึง report 7 วันล่าสุด",
        schema({"campaign_id": {"type": "string"}, "ad_account_id": {"type": "string"}, "level": {"type": "string", "default": "CAMPAIGN"}}),
        get_weekly_report,
    ),
    "list_audiences": (
        "ดึงรายการ custom audiences",
        schema({"ad_account_id": {"type": "string"}}),
        list_audiences,
    ),
    "list_advanced_targeting_codes": (
        "ดึง official advanced targeting codes สำหรับ interest/behavior/status ก่อนสร้าง manual targeting",
        schema(
            {
                "campaign_objective": {"type": "string", "default": "GAIN_FRIENDS"},
                "country": {"type": "string", "default": "TH"},
                "locale": {"type": "string", "default": "th"},
            }
        ),
        list_advanced_targeting_codes,
    ),
    "create_audience": (
        "สร้าง custom audience ใหม่ แบบ dry_run เป็นค่าเริ่มต้น",
        schema(
            {
                "name": {"type": "string"},
                "type": {"type": "string", "enum": ["CUSTOMER_LIST", "WEBSITE", "APP", "ENGAGEMENT"]},
                "ad_account_id": {"type": "string"},
                "dry_run": {"type": "boolean", "default": True},
            },
            ["name", "type"],
        ),
        create_audience,
    ),
}


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(name=name, description=description, inputSchema=input_schema)
        for name, (description, input_schema, _func) in TOOLS.items()
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    if name not in TOOLS:
        result = {"ok": False, "message": f"ไม่รู้จัก tool: {name}"}
    else:
        _description, _input_schema, func = TOOLS[name]
        result = await func(**(arguments or {}))
    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2),
        )
    ]


async def main() -> None:
    async with stdio_server() as streams:
        await server.run(*streams, server.create_initialization_options())


def cli() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    cli()
