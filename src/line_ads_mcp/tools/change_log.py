"""Best-effort write audit logging and entity readback helpers."""

from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
import inspect
import json
import os
from pathlib import Path
from typing import Any

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient, LineAdsConfig

from .common import handle_tool_error, ok
from .entities import fetch_entity

_current_change: ContextVar[dict[str, Any] | None] = ContextVar("line_ads_change", default=None)


def append_change(workspace_dir: str | None, record: dict[str, Any]) -> str | None:
    """Append one UTF-8 JSON line; return its path, or None without a workspace.

    Invalid paths and I/O errors are raised for the caller to report separately
    from the API result. Never create the workspace directory itself.
    """
    directory = workspace_dir if workspace_dir is not None else os.getenv("LINE_ADS_WORKSPACE_DIR")
    if directory is None:
        return None
    root = Path(directory)
    if not root.is_absolute() or not root.is_dir():
        raise ValueError("workspace_dir must be an absolute existing directory")
    line = json.dumps(record, ensure_ascii=False) + "\n"
    destination = root / "line-ads-data" / "change_log.jsonl"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as stream:
        stream.write(line)
    return str(destination)


def track_change(entity_type: str, id_parameter: str | None = None):
    """Log each public real-write invocation once, including validation failures.

    Pause/resume delegate to update tools; the outer invocation owns the record.
    Context-local state keeps concurrent tool calls independent.
    """
    def decorate(function):
        signature = inspect.signature(function)

        @wraps(function)
        async def wrapped(*args, **kwargs):
            arguments = signature.bind(*args, **kwargs)
            arguments.apply_defaults()
            values = arguments.arguments
            if type(values["dry_run"]) is not bool:
                # Only an explicit False may write; None/0/"" must never reach the API.
                return {"ok": False, "error_code": "VALIDATION_ERROR",
                        "message": "dry_run ต้องเป็น true หรือ false เท่านั้น"}
            if values["dry_run"] or _current_change.get() is not None:
                return await function(*args, **kwargs)
            record = {
                "tool": function.__name__,
                "ad_account_id": values.get("ad_account_id") or os.getenv("LINE_ADS_AD_ACCOUNT_ID"),
                "entity_type": entity_type,
                "entity_id": values.get(id_parameter) if id_parameter else None,
                "endpoint": None,
                "payload": {},
                "before": None,
                "after": None,
                "readback_ok": None,
            }
            token = _current_change.set(record)
            try:
                try:
                    result = await function(*args, **kwargs)
                except Exception as error:
                    result = handle_tool_error(error)
                record.update(
                    ts=datetime.now(timezone.utc).isoformat(),
                    ok=result.get("ok", False),
                    error=None if result.get("ok") else dict(result),
                )
                try:
                    path = append_change(values.get("workspace_dir"), record)
                    result["change_log"] = path if path is not None else "skipped (no workspace_dir)"
                except Exception as error:
                    result["change_log_error"] = str(error)
                return result
            finally:
                _current_change.reset(token)

        return wrapped
    return decorate


def set_change_context(**values: Any) -> None:
    record = _current_change.get()
    if record is not None:
        record.update(values)


# Read-only fields of Campaign/Adgroup/Ad in LINE Ads API v3.12.3 (id is kept: it matches the path).
READ_ONLY_FIELDS = {
    "deliveryStatus",
    "deliveryStatusReasons",
    "createdDate",
    "modifiedDate",
    "removedDate",
    "adgroupLearning",
    "firstAutoBidConversionId",
}


def merge_update_body(before: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    """Build a full update body: the current entity minus read-only fields, then the approved changes.

    The v3 update endpoints take the whole entity (e.g. Ad requires adgroupId, name and creative),
    so sending only the changed fields could be rejected or reset fields we did not mean to touch.
    """
    body = {key: value for key, value in before.items() if key not in READ_ONLY_FIELDS}
    for key, value in changes.items():
        if key == "targeting" and isinstance(value, dict) and isinstance(body.get(key), dict):
            # Keep targeting sub-keys the change did not mention (e.g. interests when only age changes).
            body[key] = {**body[key], **value}
        else:
            body[key] = value
    return body


def _snapshot(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "configured_status": row.get("configuredStatus"),
        "delivery_status": row.get("deliveryStatus"),
        **{key: value for key, value in row.items() if "budget" in key.lower() or "bid" in key.lower()},
    }


def _created_id(data: Any) -> Any:
    if isinstance(data, dict):
        if data.get("id") is not None:
            return data["id"]
        rows = data.get("datas")
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            return rows[0].get("id")
    return None


async def write_entity(
    config: LineAdsConfig,
    account_id: str,
    entity_type: str,
    endpoint: str,
    payload: dict[str, Any],
    entity_id: str | None = None,
) -> dict[str, Any]:
    """Read before updating, write once, then read back on the same client.

    A failed readback never masks a successful POST. Mismatches contain API
    field names; money and bid values are compared in their original API units.
    """
    set_change_context(ad_account_id=account_id, endpoint=endpoint, payload=payload)
    before = None
    changes = payload
    async with LineAdsClient(config) as client:
        if entity_id is not None:
            before = await fetch_entity(client, account_id, entity_type, entity_id)
            set_change_context(before=before)
            if before is None:
                raise LineAdsAPIError(404, f"ไม่พบ {entity_type} ID: {entity_id}", "NOT_FOUND")
            payload = merge_update_body(before, payload)
            set_change_context(payload=payload)
        data = await client.post(endpoint, payload)
        result = ok(data)
        if entity_id is not None:
            result["before"] = before
        written_id = entity_id if entity_id is not None else _created_id(data)
        set_change_context(entity_id=written_id)
        result.update(readback=None, readback_ok=None, readback_mismatch=[])
        try:
            if written_id is None:
                raise ValueError("API response did not contain a created entity id")
            row = await fetch_entity(client, account_id, entity_type, written_id)
            if row is None:
                raise ValueError(f"Readback entity not found: {written_id}")
            snapshot = _snapshot(row)
            fields = [key for key in changes if key == "configuredStatus" or (
                entity_id is not None and ("budget" in key.lower() or "bid" in key.lower())
            )]
            mismatches = [key for key in fields if key not in row or row[key] != changes[key]]
            result.update(readback=snapshot, readback_ok=not mismatches, readback_mismatch=mismatches)
            set_change_context(after=snapshot, readback_ok=not mismatches)
        except Exception as error:
            result["readback_error"] = str(error)
        return result
