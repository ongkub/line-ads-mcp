"""Shared helpers for LINE Ads tools."""

from __future__ import annotations

from typing import Any

from line_ads_mcp.client import LineAdsAPIError


def to_micro(amount: float) -> int:
    """Convert a THB amount to LINE Ads micro-units (1 THB = 1,000,000 micro)."""
    return int(round(amount * 1_000_000))


def clean_dict(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def ok(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def dry_run_response(action: str, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "dry_run": True,
        "message": "dry_run=True จึงยังไม่ได้ส่งคำสั่งไป LINE Ads API",
        "action": action,
        "endpoint": endpoint,
        "payload": payload,
    }


def handle_tool_error(error: Exception) -> dict[str, Any]:
    if isinstance(error, LineAdsAPIError):
        return error.to_dict()
    return {"ok": False, "message": f"เกิดข้อผิดพลาด: {error}"}


def require_one_of(value: str, allowed: set[str], field: str) -> None:
    if value not in allowed:
        raise LineAdsAPIError(
            400,
            f"{field} ต้องเป็นค่าใดค่าหนึ่ง: {', '.join(sorted(allowed))}",
            "VALIDATION_ERROR",
        )

