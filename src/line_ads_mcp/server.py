"""MCP server entry point for LINE Ads tools."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from line_ads_mcp.tools.ads import create_ad, get_ad_status, list_ads, pause_ad, resume_ad, upload_media
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
from line_ads_mcp.tools.csv_sync import sync_ad_daily_csv
from line_ads_mcp.tools.customer_lists import get_customer_list_upload_status, upload_customer_list
from line_ads_mcp.tools.entities import get_entity
from line_ads_mcp.tools.reach import estimate_adset_reach
from line_ads_mcp.tools.reports import get_daily_report, get_report, get_weekly_report
from line_ads_mcp.tools.spend_caps import check_spend_cap

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
        "อ่านอย่างเดียว: รายการ campaign ทั้งบัญชี ดึงทุกหน้าเป็นค่าเริ่มต้น กรอง configuredStatus ในผลลัพธ์ตาม status",
        schema(
            {
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "status": {
                    "anyOf": [{"type": "string", "enum": ["ACTIVE", "PAUSED", "REMOVED"]}, {"type": "null"}],
                    "default": None,
                },
                "fetch_all": {"type": "boolean", "default": True},
                "page": {"type": "integer", "default": 1, "minimum": 1},
                "size": {
                    "type": "integer",
                    "default": 100,
                    "minimum": 1,
                    "description": "จำนวนแถวต่อหน้า; fetch_all=True จำกัดไม่เกิน 100",
                },
            },
            [],
        ),
        list_campaigns,
    ),
    "create_campaign": (
        "เขียน: สร้าง campaign โดย status=PAUSED และ dry_run=True เป็นค่าเริ่มต้น ต้องระบุ start_date ก่อนสร้างจริง; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false",
        schema(
            {
                "name": {"type": "string"},
                "objective": {
                    "type": "string",
                    "enum": ["APP_INSTALL", "GAIN_FRIENDS", "REACH", "VIDEO_VIEW", "VISIT_MY_WEBSITE", "WEBSITE_CONVERSION"],
                },
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "daily_budget": {
                    "type": ["number", "null"],
                    "default": None,
                    "description": "จำนวนเงินหน่วย THB ต้องรับค่าจากผู้ใช้ ห้ามเดา",
                },
                "total_budget": {
                    "type": ["number", "null"],
                    "default": None,
                    "description": "จำนวนเงินหน่วย THB ต้องรับค่าจากผู้ใช้ ห้ามเดา",
                },
                "start_date": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "วันเวลาเริ่ม campaign แบบ ISO เช่น 2026-05-14T09:00:00+07:00; ฟังก์ชันตรวจว่าต้องระบุแม้ default=None",
                },
                "end_date": {"type": ["string", "null"], "default": None},
                "dry_run": {"type": "boolean", "default": True},
                "status": {"type": "string", "enum": ["ACTIVE", "PAUSED"], "default": "PAUSED"},
                "workspace_dir": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "โฟลเดอร์ทำงาน absolute path ที่มีอยู่แล้ว สำหรับ line-ads-data/change_log.jsonl; ไม่ระบุใช้ LINE_ADS_WORKSPACE_DIR",
                },
            },
            ["name", "objective"],
        ),
        create_campaign,
    ),
    "update_campaign": (
        "เขียน: แก้ชื่อ งบต่อวัน หรือสถานะ campaign; dry_run=True เป็นค่าเริ่มต้น; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false",
        schema(
            {
                "campaign_id": {"type": ["string", "integer"]},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "status": {
                    "anyOf": [{"type": "string", "enum": ["ACTIVE", "PAUSED"]}, {"type": "null"}],
                    "default": None,
                },
                "daily_budget": {
                    "type": ["number", "null"],
                    "default": None,
                    "description": "จำนวนเงินหน่วย THB ต้องรับค่าจากผู้ใช้ ห้ามเดา",
                },
                "name": {"type": ["string", "null"], "default": None},
                "dry_run": {"type": "boolean", "default": True},
                "workspace_dir": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "โฟลเดอร์ทำงาน absolute path ที่มีอยู่แล้ว สำหรับ line-ads-data/change_log.jsonl; ไม่ระบุใช้ LINE_ADS_WORKSPACE_DIR",
                },
            },
            ["campaign_id"],
        ),
        update_campaign,
    ),
    "pause_campaign": (
        "เขียน: หยุด campaign ชั่วคราว; dry_run=True เป็นค่าเริ่มต้น; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false",
        schema(
            {
                "campaign_id": {"type": ["string", "integer"]},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "dry_run": {"type": "boolean", "default": True},
                "workspace_dir": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "โฟลเดอร์ทำงาน absolute path ที่มีอยู่แล้ว สำหรับ line-ads-data/change_log.jsonl; ไม่ระบุใช้ LINE_ADS_WORKSPACE_DIR",
                },
            },
            ["campaign_id"],
        ),
        pause_campaign,
    ),
    "resume_campaign": (
        "เขียน: เปิด campaign กลับมาทำงาน; dry_run=True เป็นค่าเริ่มต้น; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false",
        schema(
            {
                "campaign_id": {"type": ["string", "integer"]},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "dry_run": {"type": "boolean", "default": True},
                "workspace_dir": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "โฟลเดอร์ทำงาน absolute path ที่มีอยู่แล้ว สำหรับ line-ads-data/change_log.jsonl; ไม่ระบุใช้ LINE_ADS_WORKSPACE_DIR",
                },
            },
            ["campaign_id"],
        ),
        resume_campaign,
    ),
    "list_adsets": (
        "อ่านอย่างเดียว: รายการ ad set/adgroup ทั้งบัญชี หรือกรอง campaign_id ดึงทุกหน้าเป็นค่าเริ่มต้น กรอง configuredStatus ตาม status",
        schema(
            {
                "campaign_id": {"type": ["string", "integer", "null"], "default": None},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "status": {
                    "anyOf": [{"type": "string", "enum": ["ACTIVE", "PAUSED", "REMOVED"]}, {"type": "null"}],
                    "default": None,
                },
                "fetch_all": {"type": "boolean", "default": True},
                "page": {"type": "integer", "default": 1, "minimum": 1},
                "size": {
                    "type": "integer",
                    "default": 100,
                    "minimum": 1,
                    "description": "จำนวนแถวต่อหน้า; fetch_all=True จำกัดไม่เกิน 100",
                },
            },
            [],
        ),
        list_adsets,
    ),
    "create_adset": (
        "เขียน: สร้าง ad set/adgroup โดย status=PAUSED และ dry_run=True เป็นค่าเริ่มต้น; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false",
        schema(
            {
                "campaign_id": {"type": ["string", "integer"]},
                "name": {"type": "string"},
                "bid_type": {
                    "type": "string",
                    "enum": ["CPC", "CPF", "CPM", "CPV"],
                    "description": "CPF สำหรับ GAIN_FRIENDS",
                },
                "bid_strategy": {
                    "type": "string",
                    "enum": ["COST_CAP", "LOWEST_COST"],
                    "description": "COST_CAP ต้องระบุ bid_amount ด้วย",
                },
                "auto_bid_type": {
                    "type": "string",
                    "enum": ["CLICK", "FRIEND", "INSTALL", "REACH", "VIDEO_VIEW"],
                    "description": "FRIEND สำหรับ GAIN_FRIENDS+CPF",
                },
                "daily_budget": {"type": "number", "description": "จำนวนเงินหน่วย THB ต้องรับค่าจากผู้ใช้ ห้ามเดา"},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "bid_amount": {
                    "type": ["number", "null"],
                    "default": None,
                    "description": "จำนวนเงินหน่วย THB ต้องรับค่าจากผู้ใช้ ห้ามเดา",
                },
                "age_min": {
                    "type": "integer",
                    "enum": [20, 25, 30, 35, 40, 45, 50, 55, 60, 65],
                    "default": 20,
                    "description": "อายุต่ำสุด valid: 20,25,30,...,65 (ขั้นละ 5)",
                },
                "age_max": {
                    "anyOf": [{"type": "integer", "enum": [24, 29, 34, 39, 44, 49, 54, 59, 64]}, {"type": "null"}],
                    "default": None,
                    "description": "อายุสูงสุด valid: 24,29,34,...,64 (ขั้นละ 5); ไม่ระบุ = ไม่ตั้งค่า (ไม่จำกัดอายุสูงสุด)",
                },
                "country": {"type": "string", "default": "TH"},
                "targeting_mode": {
                    "anyOf": [{"type": "string", "enum": ["AUTO", "MANUAL"]}, {"type": "null"}],
                    "default": None,
                    "description": "ถ้ามี interest_codes ให้ใช้ MANUAL; tool จะเลือกให้เองถ้าไม่ระบุ",
                },
                "genders": {"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}], "default": None},
                "interest_codes": {
                    "anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}],
                    "default": None,
                    "description": "ใช้ code จาก list_advanced_targeting_codes เช่น อาชีพและธุรกิจ=4",
                },
                "interest_groups": {
                    "anyOf": [
                        {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
                        {"type": "null"},
                    ],
                    "default": None,
                    "description": "narrow targeting: 1 list = 1 ชั้น (OR ในชั้น, AND ข้ามชั้น) ใส่ interest/behavior/purchase intent code ปนกันได้ เช่น [[\"18\", \"2479\"], [\"2444\", \"2445\"]] tool แยกเป็น interests/behaviors ให้เอง",
                },
                "behavior_codes": {
                    "anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}],
                    "default": None,
                    "description": "ใช้ code จาก list_advanced_targeting_codes เช่น มีกำลังการซื้อสูง=1590",
                },
                "excluded_audience_ids": {
                    "anyOf": [{"type": "array", "items": {"type": ["string", "integer"]}}, {"type": "null"}],
                    "default": None,
                    "description": "GAIN_FRIENDS campaigns ต้องใส่ audience ID ของเพื่อนปัจจุบัน (ดูจาก list_audiences)",
                },
                "custom_audience_ids": {"anyOf": [{"type": "array", "items": {"type": ["string", "integer"]}}, {"type": "null"}], "default": None},
                "start_date": {"type": ["string", "null"], "default": None},
                "end_date": {"type": ["string", "null"], "default": None},
                "dry_run": {"type": "boolean", "default": True},
                "status": {"type": "string", "enum": ["ACTIVE", "PAUSED"], "default": "PAUSED"},
                "workspace_dir": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "โฟลเดอร์ทำงาน absolute path ที่มีอยู่แล้ว สำหรับ line-ads-data/change_log.jsonl; ไม่ระบุใช้ LINE_ADS_WORKSPACE_DIR",
                },
            },
            ["campaign_id", "name", "bid_type", "bid_strategy", "auto_bid_type", "daily_budget"],
        ),
        create_adset,
    ),
    "update_adset": (
        "เขียน: แก้งบ bid สถานะ หรือ targeting ของ ad set/adgroup; dry_run=True เป็นค่าเริ่มต้น; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false",
        schema(
            {
                "adset_id": {"type": ["string", "integer"]},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "status": {
                    "anyOf": [{"type": "string", "enum": ["ACTIVE", "PAUSED"]}, {"type": "null"}],
                    "default": None,
                },
                "daily_budget": {
                    "type": ["number", "null"],
                    "default": None,
                    "description": "จำนวนเงินหน่วย THB ต้องรับค่าจากผู้ใช้ ห้ามเดา",
                },
                "bid_amount": {
                    "type": ["number", "null"],
                    "default": None,
                    "description": "จำนวนเงินหน่วย THB ต้องรับค่าจากผู้ใช้ ห้ามเดา",
                },
                "targeting": {"type": ["object", "null"], "default": None},
                "age_min": {
                    "anyOf": [{"type": "integer", "enum": [20, 25, 30, 35, 40, 45, 50, 55, 60, 65]}, {"type": "null"}],
                    "default": None,
                },
                "age_max": {
                    "anyOf": [{"type": "integer", "enum": [24, 29, 34, 39, 44, 49, 54, 59, 64]}, {"type": "null"}],
                    "default": None,
                },
                "country": {"type": "string", "default": "TH"},
                "targeting_mode": {"anyOf": [{"type": "string", "enum": ["AUTO", "MANUAL"]}, {"type": "null"}], "default": None},
                "genders": {"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}], "default": None},
                "interest_codes": {"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}], "default": None},
                "interest_groups": {
                    "anyOf": [
                        {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
                        {"type": "null"},
                    ],
                    "default": None,
                },
                "behavior_codes": {"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}], "default": None},
                "excluded_audience_ids": {"anyOf": [{"type": "array", "items": {"type": ["string", "integer"]}}, {"type": "null"}], "default": None},
                "custom_audience_ids": {"anyOf": [{"type": "array", "items": {"type": ["string", "integer"]}}, {"type": "null"}], "default": None},
                "dry_run": {"type": "boolean", "default": True},
                "workspace_dir": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "โฟลเดอร์ทำงาน absolute path ที่มีอยู่แล้ว สำหรับ line-ads-data/change_log.jsonl; ไม่ระบุใช้ LINE_ADS_WORKSPACE_DIR",
                },
            },
            ["adset_id"],
        ),
        update_adset,
    ),
    "pause_adset": (
        "เขียน: หยุด ad set ชั่วคราว; dry_run=True เป็นค่าเริ่มต้น; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false",
        schema(
            {
                "adset_id": {"type": ["string", "integer"]},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "dry_run": {"type": "boolean", "default": True},
                "workspace_dir": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "โฟลเดอร์ทำงาน absolute path ที่มีอยู่แล้ว สำหรับ line-ads-data/change_log.jsonl; ไม่ระบุใช้ LINE_ADS_WORKSPACE_DIR",
                },
            },
            ["adset_id"],
        ),
        pause_adset,
    ),
    "resume_adset": (
        "เขียน: เปิด ad set กลับมาทำงาน; dry_run=True เป็นค่าเริ่มต้น; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false",
        schema(
            {
                "adset_id": {"type": ["string", "integer"]},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "dry_run": {"type": "boolean", "default": True},
                "workspace_dir": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "โฟลเดอร์ทำงาน absolute path ที่มีอยู่แล้ว สำหรับ line-ads-data/change_log.jsonl; ไม่ระบุใช้ LINE_ADS_WORKSPACE_DIR",
                },
            },
            ["adset_id"],
        ),
        resume_adset,
    ),
    "upload_media": (
        "เขียน: อัปโหลดรูป JPG/PNG หรือวิดีโอ MP4/MOV; คืน image_hash สำหรับ create_ad; dry_run=True เป็นค่าเริ่มต้น; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false",
        schema(
            {
                "file_path": {"type": "string"},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "dry_run": {"type": "boolean", "default": True},
                "workspace_dir": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "โฟลเดอร์ทำงาน absolute path ที่มีอยู่แล้ว สำหรับ line-ads-data/change_log.jsonl; ไม่ระบุใช้ LINE_ADS_WORKSPACE_DIR",
                },
            },
            ["file_path"],
        ),
        upload_media,
    ),
    "create_ad": (
        "เขียน: สร้าง ad ด้วย image_hash จาก upload_media โดย status=PAUSED และ dry_run=True เป็นค่าเริ่มต้น; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false",
        schema(
            {
                "adset_id": {"type": ["string", "integer"]},
                "name": {"type": "string"},
                "image_hash": {"type": "string", "description": "imageHash ที่ได้จาก upload_media (ไม่ใช่ media_id)"},
                "title": {"type": "string", "description": "ข้อความไม่เกิน 20 ตัวอักษร", "maxLength": 20},
                "call_to_action": {
                    "type": "string",
                    "enum": ["ADD_FRIEND", "CONTACT_US", "DOWNLOAD", "LEARN_MORE", "SHOP_NOW", "SIGN_UP"],
                    "description": "ADD_FRIEND สำหรับ GAIN_FRIENDS campaign",
                },
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "campaign_id": {
                    "type": ["string", "integer", "null"],
                    "default": None,
                    "description": "campaign ID (แนะนำให้ส่งเสมอตาม LINE Ads API spec)",
                },
                "creative_format": {"type": "string", "enum": ["IMAGE", "VIDEO"], "default": "IMAGE"},
                "description": {
                    "type": ["string", "null"],
                    "default": None,
                    "maxLength": 20,
                    "description": "ข้อความไม่เกิน 20 ตัวอักษร",
                },
                "long_title": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "หัวข้อยาว — บังคับเมื่อใช้ small_image_hash (รูปเล็ก 600×400px)",
                },
                "destination_url": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "URL ปลายทาง หากระบุต้องขึ้นต้นด้วย https://",
                },
                "small_image_hash": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "imageHash ของรูปขนาดเล็ก 600×400px (แนะนำให้ใส่เสมอเพื่อเพิ่ม placement coverage)",
                },
                "dry_run": {"type": "boolean", "default": True},
                "status": {"type": "string", "enum": ["ACTIVE", "PAUSED"], "default": "PAUSED"},
                "workspace_dir": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "โฟลเดอร์ทำงาน absolute path ที่มีอยู่แล้ว สำหรับ line-ads-data/change_log.jsonl; ไม่ระบุใช้ LINE_ADS_WORKSPACE_DIR",
                },
            },
            ["adset_id", "name", "image_hash", "title", "call_to_action"],
        ),
        create_ad,
    ),
    "get_ad_status": (
        "อ่านอย่างเดียว: ตรวจสถานะ ad ด้วย exact ad_id คืน configured_status และ delivery_status; NOT_APPROVED หมายถึงไม่ผ่านการตรวจ",
        schema(
            {"ad_id": {"type": ["string", "integer"]}, "ad_account_id": {"type": ["string", "integer", "null"], "default": None}},
            ["ad_id"],
        ),
        get_ad_status,
    ),
    "list_ads": (
        "อ่านอย่างเดียว: รายการ ad ทั้งบัญชี หรือกรอง adset_id/campaign_id ดึงทุกหน้าเป็นค่าเริ่มต้น กรอง configuredStatus ตาม status",
        schema(
            {
                "adset_id": {"type": ["string", "integer", "null"], "default": None},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "campaign_id": {"type": ["string", "integer", "null"], "default": None},
                "status": {
                    "anyOf": [{"type": "string", "enum": ["ACTIVE", "DRAFT", "PAUSED", "REMOVED"]}, {"type": "null"}],
                    "default": None,
                },
                "fetch_all": {"type": "boolean", "default": True},
                "page": {"type": "integer", "default": 1, "minimum": 1},
                "size": {
                    "type": "integer",
                    "default": 100,
                    "minimum": 1,
                    "description": "จำนวนแถวต่อหน้า; fetch_all=True จำกัดไม่เกิน 100",
                },
            },
            [],
        ),
        list_ads,
    ),
    "get_report": (
        "อ่านอย่างเดียว: รายงานตามระดับและช่วงวันที่ UTC ดึงทุกหน้าเป็นค่าเริ่มต้น ตรวจ paging.complete; by_day=True ดึงแยกวัน×entity สูงสุด 93 วัน; อ่านผลตาม objective: GAIN_FRIENDS ไม่มีคอลัมน์เพื่อน ใช้ click แทนจำนวนเพื่อนใหม่ (CPF ≈ cost ÷ click), WEBSITE_CONVERSION ดู summary.conversion_events; cost เป็นบาท",
        schema(
            {
                "level": {"type": "string", "enum": ["AD", "ADGROUP", "CAMPAIGN"]},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "campaign_id": {"type": ["string", "integer", "null"], "default": None},
                "fields": {"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}], "default": None},
                "adgroup_id": {"type": ["string", "integer", "null"], "default": None},
                "fetch_all": {"type": "boolean", "default": True},
                "page_size": {"type": "integer", "default": 100, "minimum": 1, "maximum": 100},
                "max_pages": {"type": "integer", "default": 50, "minimum": 1},
                "by_day": {"type": "boolean", "default": False},
            },
            ["level", "start_date", "end_date"],
        ),
        get_report,
    ),
    "get_daily_report": (
        "อ่านอย่างเดียว: รายงานเมื่อวานตาม UTC ระดับ AD และดึงทุกหน้าเป็นค่าเริ่มต้น แยกแถวตามวัน×entity ตรวจ paging.complete",
        schema(
            {
                "level": {"type": "string", "enum": ["AD", "ADGROUP", "CAMPAIGN"], "default": "AD"},
                "campaign_id": {"type": ["string", "integer", "null"], "default": None},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "fetch_all": {"type": "boolean", "default": True},
            },
            [],
        ),
        get_daily_report,
    ),
    "get_weekly_report": (
        "อ่านอย่างเดียว: รายงาน 7 วันก่อนหน้าถึงเมื่อวานตาม UTC ระดับ CAMPAIGN และดึงทุกหน้าเป็นค่าเริ่มต้น; by_day=True แยกวัน×entity ตรวจ paging.complete",
        schema(
            {
                "level": {"type": "string", "enum": ["AD", "ADGROUP", "CAMPAIGN"], "default": "CAMPAIGN"},
                "campaign_id": {"type": ["string", "integer", "null"], "default": None},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "fetch_all": {"type": "boolean", "default": True},
                "by_day": {"type": "boolean", "default": False},
            },
            [],
        ),
        get_weekly_report,
    ),
    "list_audiences": (
        "อ่านอย่างเดียว: รายการ custom audience ทุกหน้า พร้อม status, estimated_audience_size, usable_in_adset (READY) และ active_friends_audience_id เมื่อพบเพื่อน LINE OA ปัจจุบัน",
        schema(
            {"ad_account_id": {"type": ["string", "integer", "null"], "default": None}},
            [],
        ),
        list_audiences,
    ),
    "list_advanced_targeting_codes": (
        "อ่านอย่างเดียว: ดึง official advanced targeting codes สำหรับ interest/behavior/status ก่อนสร้าง manual targeting",
        schema(
            {
                "campaign_objective": {"type": "string", "default": "GAIN_FRIENDS"},
                "country": {"type": "string", "default": "TH"},
                "locale": {"type": "string", "default": "th"},
            },
            [],
        ),
        list_advanced_targeting_codes,
    ),
    "create_audience": (
        "เขียน: สร้าง custom audience (LOOKALIKE/APP_EVENT/WEBTRAFFIC/ACCOUNT_FRIENDS/VIDEO_VIEW/IMAGE_CLICK); dry_run=True เป็นค่าเริ่มต้น; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false; audience ใช้ใน ad set ได้เมื่อ READY; ไม่รองรับอัปโหลดรายชื่อลูกค้า",
        schema(
            {
                "name": {"type": "string"},
                "function_type": {"type": "string", "enum": ["LOOKALIKE", "APP_EVENT", "WEBTRAFFIC", "ACCOUNT_FRIENDS", "VIDEO_VIEW", "IMAGE_CLICK"]},
                "config": {"type": "object"},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "dry_run": {"type": "boolean", "default": True},
                "workspace_dir": {"type": ["string", "null"], "default": None},
            },
            ["name", "function_type", "config"],
        ),
        create_audience,
    ),
    "upload_customer_list": (
        "เขียน: อัปโหลดรายชื่อลูกค้า PHONE/EMAIL/IFA จาก CSV/TXT; dry_run=True เป็นค่าเริ่มต้น; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false; ไม่ส่ง/ไม่บันทึกข้อมูลดิบ ส่งเฉพาะ hash สำหรับ PHONE/EMAIL (IFA ส่ง UUID); เจ้าของข้อมูลต้องมีความยินยอม/ฐานทางกฎหมายตาม PDPA; ยืนยันด้วยไฟล์ทดสอบเล็กก่อนใช้จริง",
        schema(
            {
                "file_path": {"type": "string", "description": "absolute path ของ CSV/TXT UTF-8"},
                "id_type": {"type": "string", "enum": ["PHONE", "EMAIL", "IFA"]},
                "audience_name": {"type": ["string", "null"], "default": None},
                "audience_id": {"type": ["string", "integer", "null"], "default": None},
                "action": {"type": "string", "enum": ["ADD", "REPLACE"], "default": "ADD"},
                "column": {"type": ["string", "null"], "default": None},
                "default_country_code": {"type": "string", "default": "66"},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "dry_run": {"type": "boolean", "default": True},
                "workspace_dir": {"type": ["string", "null"], "default": None},
            },
            ["file_path", "id_type"],
        ),
        upload_customer_list,
    ),
    "get_customer_list_upload_status": (
        "อ่านอย่างเดียว: ตรวจ upload job ของรายชื่อลูกค้า; FINISHED/FAILED คืองานจบ ต้องตรวจ list_audiences จน READY ก่อนใช้ใน ad set",
        schema(
            {
                "audience_id": {"type": ["string", "integer"]},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
            },
            ["audience_id"],
        ),
        get_customer_list_upload_status,
    ),
    "get_entity": (
        "อ่านอย่างเดียว: ค้น campaign/adset/ad ด้วย exact ID คืน configured_status, delivery_status, budget, bid, targeting และ raw; NOT_APPROVED หมายถึงไม่ผ่านการตรวจ ไม่มีพารามิเตอร์ dry_run",
        schema(
            {
                "entity_type": {"type": "string", "enum": ["ad", "adset", "campaign"]},
                "entity_id": {"type": ["string", "integer"]},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
            },
            ["entity_type", "entity_id"],
        ),
        get_entity,
    ),
    "estimate_adset_reach": (
        "อ่านอย่างเดียว: ประเมินช่วง reach และ clicks ผ่าน LINE Adgroup Result Simulator พร้อม absent/invalid/ignored fields; ARS ใช้ targetingMode=MANUAL เท่านั้น (ปรับให้อัตโนมัติ); ARS รับเฉพาะ interests ใน advanced targeting — behaviors/purchaseIntents ถูกตัดออกและแจ้งใน omitted_for_simulation; ต้องระบุ bid_amount ยกเว้น bid_strategy=LOWEST_COST; ค่าประมาณ ไม่สร้างอะไร ไม่มีพารามิเตอร์ dry_run",
        schema(
            {
                "campaign_id": {"type": ["string", "integer"]},
                "campaign_objective": {
                    "type": "string",
                    "enum": ["APP_INSTALL", "GAIN_FRIENDS", "REACH", "VIDEO_VIEW", "VISIT_MY_WEBSITE", "WEBSITE_CONVERSION"],
                },
                "daily_budget": {"type": "number", "description": "จำนวนเงินหน่วย THB ต้องรับค่าจากผู้ใช้ ห้ามเดา"},
                "bid_type": {"type": "string", "enum": ["CPC", "CPF", "CPM"]},
                "auto_bid_type": {"type": "string", "enum": ["CLICK", "FRIEND", "INSTALL", "REACH", "VIDEO_VIEW"]},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "adset_id": {"type": ["string", "integer", "null"], "default": None},
                "bid_amount": {
                    "type": ["number", "null"],
                    "default": None,
                    "description": "จำนวนเงินหน่วย THB ต้องรับค่าจากผู้ใช้ ห้ามเดา",
                },
                "bid_strategy": {
                    "anyOf": [{"type": "string", "enum": ["COST_CAP", "LOWEST_COST"]}, {"type": "null"}],
                    "default": None,
                },
                "targeting": {"type": ["object", "null"], "default": None},
                "age_min": {
                    "anyOf": [{"type": "integer", "enum": [20, 25, 30, 35, 40, 45, 50, 55, 60, 65]}, {"type": "null"}],
                    "default": None,
                },
                "age_max": {
                    "anyOf": [{"type": "integer", "enum": [24, 29, 34, 39, 44, 49, 54, 59, 64]}, {"type": "null"}],
                    "default": None,
                },
                "genders": {"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}], "default": None},
                "interest_codes": {"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}], "default": None},
                "custom_audience_ids": {"anyOf": [{"type": "array", "items": {"type": ["string", "integer"]}}, {"type": "null"}], "default": None},
                "excluded_audience_ids": {"anyOf": [{"type": "array", "items": {"type": ["string", "integer"]}}, {"type": "null"}], "default": None},
                "country": {"type": "string", "default": "TH"},
            },
            ["campaign_id", "campaign_objective", "daily_budget", "bid_type", "auto_bid_type"],
        ),
        estimate_adset_reach,
    ),
    "pause_ad": (
        "เขียน: หยุด ad ชั่วคราว; dry_run=True เป็นค่าเริ่มต้น; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false",
        schema(
            {
                "ad_id": {"type": ["string", "integer"]},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "dry_run": {"type": "boolean", "default": True},
                "workspace_dir": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "โฟลเดอร์ทำงาน absolute path ที่มีอยู่แล้ว สำหรับ line-ads-data/change_log.jsonl; ไม่ระบุใช้ LINE_ADS_WORKSPACE_DIR",
                },
            },
            ["ad_id"],
        ),
        pause_ad,
    ),
    "resume_ad": (
        "เขียน: เปิด ad กลับมาทำงาน; dry_run=True เป็นค่าเริ่มต้น; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false",
        schema(
            {
                "ad_id": {"type": ["string", "integer"]},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "dry_run": {"type": "boolean", "default": True},
                "workspace_dir": {
                    "type": ["string", "null"],
                    "default": None,
                    "description": "โฟลเดอร์ทำงาน absolute path ที่มีอยู่แล้ว สำหรับ line-ads-data/change_log.jsonl; ไม่ระบุใช้ LINE_ADS_WORKSPACE_DIR",
                },
            },
            ["ad_id"],
        ),
        resume_ad,
    ),
    "check_spend_cap": (
        "อ่านอย่างเดียว: เทียบยอดใช้จ่ายกับ cap_amount ตามวันที่ UTC; exceeded เมื่อ spend > cap, within_cap เมื่อข้อมูลครบและไม่เกิน, indeterminate เมื่อข้อมูลไม่ครบและยังพิสูจน์ว่าเกินไม่ได้; period_end ใช้คาดการณ์ ไม่ pause และไม่มีพารามิเตอร์ dry_run",
        schema(
            {
                "cap_amount": {"type": "number", "description": "จำนวนเงินหน่วย THB ต้องรับค่าจากผู้ใช้ ห้ามเดา"},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "campaign_id": {"type": ["string", "integer", "null"], "default": None},
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "period_end": {"type": ["string", "null"], "default": None},
            },
            ["cap_amount", "start_date", "end_date"],
        ),
        check_spend_cap,
    ),
    "sync_ad_daily_csv": (
        "เขียนไฟล์ในเครื่องสำหรับ scheduled task บทที่ 2: upsert line-ads-data/ad_daily.csv ด้วย date+ad_id และเพิ่ม run_log.csv; วันที่รายงานเป็น UTC; dry_run=True เป็นค่าเริ่มต้น ดึงรายงานเพื่อแสดง preview แต่ไม่เขียนไฟล์ ไม่แก้บัญชีโฆษณา; ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false",
        schema(
            {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "workspace_dir": {
                    "type": "string",
                    "description": "โฟลเดอร์ทำงาน absolute path ที่มีอยู่แล้ว สำหรับ CSV และ run_log",
                },
                "ad_account_id": {"type": ["string", "integer", "null"], "default": None},
                "campaign_id": {"type": ["string", "integer", "null"], "default": None},
                "account_timezone": {"type": ["string", "null"], "default": None},
                "currency": {"type": ["string", "null"], "default": None},
                "dry_run": {"type": "boolean", "default": True},
            },
            ["start_date", "end_date", "workspace_dir"],
        ),
        sync_ad_daily_csv,
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
        normalized = dict(arguments or {})
        for key, value in normalized.items():
            if key.endswith("_id") and type(value) is int:
                normalized[key] = str(value)
            elif key.endswith("_ids") and isinstance(value, list):
                normalized[key] = [str(item) if type(item) is int else item for item in value]
        result = await func(**normalized)
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
