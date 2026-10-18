"""In-memory customer-list uploads. ยืนยันด้วยไฟล์ทดสอบเล็กก่อนใช้จริง."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
from io import BytesIO
from pathlib import Path
import re
import unicodedata
from typing import Any, Iterator

import httpx

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient, LineAdsConfig, resolve_ad_account_id

from .audiences import _reject_rate_limit
from .change_log import set_change_context, track_change
from .common import ok

ID_TYPES = {"PHONE", "EMAIL", "IFA"}
ACTIONS = {"ADD", "REPLACE"}
API_ID_TYPES = {"PHONE": "HASHED_PHONE_NUMBER", "EMAIL": "HASHED_EMAIL", "IFA": "IFA"}
MAX_FILE_BYTES = 62_914_560
MAX_INPUT_BYTES = 200 * 1024 * 1024
MAX_ROWS = 5_000_000
MAX_VALUE_CHARS = 10_000
_HASH = re.compile(r"[0-9a-fA-F]{64}\Z")
_EMAIL = re.compile(r"[^\s@]+@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}\Z")
_IFA = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z")
_HEADERS = {
    "PHONE": {"phone", "tel", "mobile", "telephone", "msisdn"},
    "EMAIL": {"email", "mail", "อีเมล"},
    "IFA": {"ifa", "adid", "idfa", "gaid"},
}


class _ValidationError(ValueError):
    """Only fixed, privacy-safe validation messages may escape the pipeline."""


def normalize_phone(value: str, default_country_code: str = "66") -> str:
    """Return country code + national number, using ASCII digits only."""
    value = unicodedata.normalize("NFKC", value).strip()
    value = re.sub(r"[\s\-.()/]", "", value)
    if value.startswith("+"):
        value = value[1:]
    elif value.startswith("00"):
        value = value[2:]
    elif value.startswith("0"):
        value = default_country_code + value[1:]
    elif default_country_code == "66" and re.fullmatch(r"(?:[689][0-9]{8}|[2-7][0-9]{7})", value):
        # Excel often drops the leading 0 of Thai numbers (0812345678 -> 812345678).
        value = "66" + value
    if not re.fullmatch(r"[0-9]+", value):
        raise _ValidationError("เบอร์โทรต้องเป็นตัวเลข")
    if value.startswith("66"):
        if not re.fullmatch(r"(?:[689][0-9]{8}|[2-7][0-9]{7})", value[2:]):
            raise _ValidationError("เบอร์ไทยผิดรูปแบบ")
    elif not 8 <= len(value) <= 15:
        raise _ValidationError("เบอร์โทรต้องมี 8–15 หลัก")
    return value


def normalize_email(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).strip().lower()
    if len(value) > 120:
        raise _ValidationError("อีเมลยาวเกิน 120 ตัวอักษร")
    if not _EMAIL.fullmatch(value):
        raise _ValidationError("อีเมลผิดรูปแบบ")
    return value


def normalize_ifa(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).strip().lower()
    if not _IFA.fullmatch(value):
        raise _ValidationError("IFA ต้องเป็น UUID")
    return value


def _normalize(value: str, id_type: str, country_code: str) -> tuple[str, bool]:
    value = unicodedata.normalize("NFKC", value).strip()
    if id_type != "IFA" and _HASH.fullmatch(value):
        return value.lower(), True
    if id_type == "PHONE":
        value = normalize_phone(value, country_code)
    elif id_type == "EMAIL":
        value = normalize_email(value)
    else:
        return normalize_ifa(value), False
    return hashlib.sha256(value.encode("utf-8")).hexdigest(), False


def _mask(value: str, id_type: str) -> str:
    value = unicodedata.normalize("NFKC", value).strip().lower()
    if id_type == "PHONE":
        digits = re.sub(r"[^0-9]", "", value)
        return digits[:2] + "*****" + digits[-3:] if len(digits) > 5 else "***"
    if id_type == "EMAIL" and value.count("@") == 1:
        local, domain = value.split("@")
        if local and len(domain) <= 60 and _EMAIL.fullmatch("x@" + domain) and not re.search(r"[0-9a-f]{64}", domain):
            return local[0] + "***@" + domain
    return "***"


def _is_header(value: str, id_type: str) -> bool:
    value = unicodedata.normalize("NFKC", value).strip().lower()
    tokens = set(re.split(r"[^a-z0-9\u0e00-\u0e7f]+", value))
    if id_type == "PHONE":
        if "โทรสาร" in value:
            return False
        if "เบอร์" in value or value.startswith(("โทรศัพท์", "มือถือ", "เบอร์โทร")):
            return True
    return bool(tokens & _HEADERS[id_type])


def _is_data(value: str, id_type: str, country_code: str) -> bool:
    if len(value) > MAX_VALUE_CHARS:
        return False
    if _HASH.fullmatch(value.strip()):
        return True
    try:
        _normalize(value, id_type, country_code)
        return True
    except _ValidationError:
        return False


def _safe_header(value: str, index: int, country_code: str) -> str:
    # Check the entire cell before truncating: whitespace and long prefixes must
    # never disguise identifiers or full hashes in metadata/errors.
    normalized = unicodedata.normalize("NFKC", value).strip()
    if (len(value) > MAX_VALUE_CHARS or re.search(r"[0-9a-fA-F]{64}", normalized)
            or any(_is_data(normalized, kind, country_code) for kind in ID_TYPES)):
        return f"(คอลัมน์ที่ {index + 1})"
    return value[:120]


def _bounded_lines(stream) -> Iterator[str]:
    while True:
        line = stream.readline(MAX_VALUE_CHARS + 3)
        if not line:
            return
        if len(line.rstrip("\r\n")) > MAX_VALUE_CHARS:
            raise _ValidationError("ค่ายาวผิดปกติ")
        yield line


def _rows(path: Path, column: str | None, id_type: str,
          country_code: str) -> Iterator[tuple[int, str, str | None]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        lines = _bounded_lines(stream)
        if path.suffix.lower() == ".txt":
            if column is not None:
                raise _ValidationError("column ใช้ได้เฉพาะไฟล์ CSV")
            for row, value in enumerate(lines, 1):
                yield row, value.rstrip("\r\n"), None
            return
        reader = csv.reader(lines, strict=True)
        headers = next(reader, [])
        if not headers:
            return
        if any(len(value) > MAX_VALUE_CHARS for value in headers):
            raise _ValidationError("ค่ายาวผิดปกติ")
        if column is not None and re.fullmatch(r"[1-9][0-9]*", column):
            candidates = [int(column) - 1] if int(column) <= len(headers) else []
        elif column is not None:
            candidates = [index for index, header in enumerate(headers) if header == column]
        elif len(headers) == 1:
            candidates = [0]
        else:
            candidates = [index for index, header in enumerate(headers) if _is_header(header, id_type)]
        if len(candidates) != 1:
            safe_headers = [_safe_header(header, index, country_code)
                            for index, header in enumerate(headers[:30])]
            raise _ValidationError(f"กรุณาระบุ column ให้ชัดเจน; headers: {safe_headers}")
        index = candidates[0]
        first = headers[index]
        headerless = not _is_header(first, id_type) and _is_data(first, id_type, country_code)
        selected = f"column {index + 1}" if headerless else _safe_header(first, index, country_code)
        if headerless:
            yield reader.line_num, first, selected
        for values in reader:
            if len(values) > len(headers):
                raise _ValidationError("จำนวนคอลัมน์ CSV ไม่ตรงกับ header")
            if any(len(value) > MAX_VALUE_CHARS for value in values):
                raise _ValidationError("ค่ายาวผิดปกติ")
            yield reader.line_num, values[index] if index < len(values) else "", selected


def _prepare(file_path: str, id_type: str, column: str | None, country_code: str) -> tuple[dict[str, Any], bytes]:
    path = Path(file_path)
    if not path.is_absolute():
        raise _ValidationError("file_path ต้องเป็น absolute path")
    if path.suffix.lower() == ".xlsx":
        raise _ValidationError("กรุณา export ไฟล์ Excel เป็น CSV ก่อนอัปโหลด")
    if path.suffix.lower() not in {".csv", ".txt"}:
        raise _ValidationError("รองรับเฉพาะ CSV หรือ TXT แบบ UTF-8")
    if not path.is_file():
        raise _ValidationError("ไม่พบไฟล์รายชื่อลูกค้า")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise _ValidationError("ไฟล์ต้นฉบับเกิน 200 MB กรุณาแบ่งไฟล์")
    stats: dict[str, Any] = dict(rows_read=0, valid=0, invalid=0, invalid_by_reason={},
                                invalid_samples=[], duplicates=0, blank=0, prehashed=0, column_used=None)
    unique: set[str] = set()
    for row, raw, selected in _rows(path, column, id_type, country_code):
        if stats["rows_read"] >= MAX_ROWS:
            raise _ValidationError("ไฟล์เกินจำนวนแถวที่รองรับ กรุณาแบ่งไฟล์")
        stats["rows_read"] += 1
        stats["column_used"] = selected
        if not unicodedata.normalize("NFKC", raw).strip():
            stats["blank"] += 1
            continue
        try:
            value, prehashed = _normalize(raw, id_type, country_code)
        except _ValidationError as error:
            reason = str(error)
            stats["invalid"] += 1
            stats["invalid_by_reason"][reason] = stats["invalid_by_reason"].get(reason, 0) + 1
            if len(stats["invalid_samples"]) < 5:
                stats["invalid_samples"].append({"row": row, "masked": _mask(raw, id_type), "reason": reason})
            continue
        stats["prehashed"] += int(prehashed)
        if value in unique:
            stats["duplicates"] += 1
            continue
        unique.add(value)
        stats["valid"] += 1
        if stats["valid"] * (37 if id_type == "IFA" else 65) > MAX_FILE_BYTES:
            raise _ValidationError("ไฟล์ที่สร้างเกิน 62,914,560 bytes กรุณาแบ่งไฟล์แล้วอัปโหลดทีละส่วน")
    if not unique:
        raise _ValidationError("ไม่มีข้อมูลที่ถูกต้องสำหรับอัปโหลด (valid = 0)")
    with BytesIO() as output:
        for value in sorted(unique):
            output.write(value.encode("ascii") + b"\n")
        content = output.getvalue()
    stats.update(file_bytes=len(content), within_size_limit=len(content) <= MAX_FILE_BYTES)
    return stats, content


def _safe_error(error: Exception) -> dict[str, Any]:
    if isinstance(error, _ValidationError):
        return {"ok": False, "error_code": "VALIDATION_ERROR", "message": str(error)}
    if isinstance(error, (UnicodeError, csv.Error)):
        message = "ไฟล์ต้องเป็น CSV/TXT แบบ UTF-8 ที่ถูกต้อง"
    elif isinstance(error, LineAdsAPIError):
        # API error text may echo uploaded values. Never return/log that text.
        return {"ok": False, "status_code": error.status_code,
                "error_code": "RATE_LIMIT" if error.status_code == 429 else "API_ERROR",
                "message": "LINE Ads API ไม่สามารถดำเนินการได้ กรุณาตรวจสอบสิทธิ์/ข้อมูล หรือลองใหม่ภายหลัง"}
    else:
        message = "ไม่สามารถประมวลผลรายชื่อลูกค้าได้ กรุณาตรวจสอบไฟล์และการตั้งค่า"
    return {"ok": False, "message": message}


@track_change("audience")
async def upload_customer_list(
    file_path: str,
    id_type: str,
    audience_name: str | None = None,
    audience_id: str | None = None,
    action: str = "ADD",
    column: str | None = None,
    default_country_code: str = "66",
    ad_account_id: str | None = None,
    dry_run: bool = True,
    workspace_dir: str | None = None,
) -> dict[str, Any]:
    """Normalize and hash only in memory. ยืนยันด้วยไฟล์ทดสอบเล็กก่อนใช้จริง.

    PHONE/EMAIL use lowercase SHA-256; IFA stays a normalized UUID.
    CSV column accepts a header name or a 1-based index (e.g. "1").
    Multi-column headerless CSV requires an explicit column index. A first
    candidate cell that is an identifier/hash, rather than a header, is data.
    Input limits: 200 MB, 5,000,000 data rows, 10,000 chars per line/cell.
    Requires consent/a lawful PDPA basis and user confirmation after dry run.
    """
    try:
        if type(dry_run) is not bool:
            raise _ValidationError("dry_run ต้องเป็น bool (true/false) เท่านั้น")
        if not isinstance(id_type, str) or id_type not in ID_TYPES:
            raise _ValidationError("id_type ต้องเป็น PHONE, EMAIL หรือ IFA")
        if not isinstance(action, str) or action not in ACTIONS:
            raise _ValidationError("action ต้องเป็น ADD หรือ REPLACE")
        if (audience_name is None) == (audience_id is None):
            raise _ValidationError("ระบุ audience_name หรือ audience_id อย่างใดอย่างหนึ่งเท่านั้น")
        if audience_name is not None and (not isinstance(audience_name, str) or not audience_name.strip()):
            raise _ValidationError("audience_name ต้องไม่ว่าง")
        if audience_id is not None and (not isinstance(audience_id, str) or not re.fullmatch(r"[0-9]+", audience_id)):
            raise _ValidationError("audience_id ต้องเป็นตัวเลข")
        if action == "REPLACE" and audience_id is None:
            raise _ValidationError("REPLACE ต้องระบุ audience_id ของ audience เดิม")
        if not isinstance(default_country_code, str) or not re.fullmatch(r"[1-9][0-9]{0,2}", default_country_code):
            raise _ValidationError("default_country_code ต้องเป็นรหัสประเทศ 1–3 หลัก ไม่มี +")
        stats, content = _prepare(file_path, id_type, column, default_country_code)
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        endpoint = f"/adaccounts/{account_id}/custom-audiences/upload"
        if dry_run:
            return ok({"dry_run": True, "endpoint": endpoint, "id_type": id_type,
                       "api_id_type": API_ID_TYPES[id_type], "action": action,
                       "audience": audience_name if audience_name is not None else audience_id, **stats,
                       "note": "ข้อมูลดิบไม่ถูกส่งหรือบันทึก ส่งเฉพาะค่า hash SHA-256" if id_type != "IFA" else
                       "ข้อมูล IFA ส่งเป็น UUID ที่ปรับรูปแบบแล้ว ไม่ hash; ข้อมูลดิบไม่ถูกบันทึก"})
        counts = {key: stats[key] for key in ("rows_read", "valid", "invalid", "duplicates", "blank", "prehashed", "file_bytes")}
        identity = {"name": audience_name} if audience_name is not None else {"id": audience_id}
        set_change_context(ad_account_id=account_id, endpoint=endpoint,
                           payload={**counts, "id_type": id_type, "action": action, **identity})
        files = {key: (None, value) for key, value in {**identity, "action": action, "idType": API_ID_TYPES[id_type]}.items()}
        files["file"] = ("customer_list.txt", content, "text/plain")
        async with httpx.AsyncClient(timeout=30, event_hooks={"response": [_reject_rate_limit]}) as http_client:
            async with LineAdsClient(config, http_client=http_client) as client:
                data = await client.request("POST", endpoint, files=files)
        # Upload responses should only contain audience metadata; do not persist
        # the server response, which could echo file content on some API errors.
        audience = {key: data[key] for key in ("id", "name", "status", "functionType", "estimatedAudienceSize") if key in data}
        set_change_context(entity_id=audience.get("id"))
        return ok({"audience": audience, "id": audience.get("id"), "status": audience.get("status"),
                   "uploaded": stats["valid"],
                   "note": "LINE กำลังประมวลผล ตรวจด้วย get_customer_list_upload_status แล้ว list_audiences จน READY ก่อนใช้ใน ad set"})
    except Exception as error:
        return _safe_error(error)


def _job_order(job: dict[str, Any]) -> tuple[float, int]:
    """Compare API timestamps chronologically, including timezone offsets."""
    created = job.get("created")
    try:
        if isinstance(created, (int, float)):
            timestamp = float(created)
        else:
            parsed = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            timestamp = parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).timestamp()
    except (ValueError, OverflowError, OSError):
        timestamp = float("-inf")
    try:
        job_id = int(job.get("job_id"))
    except (TypeError, ValueError):
        job_id = -1
    return timestamp, job_id


async def get_customer_list_upload_status(audience_id: str, ad_account_id: str | None = None) -> dict[str, Any]:
    """Read upload jobs; FINISHED is upload completion, not audience readiness."""
    try:
        if not isinstance(audience_id, str) or not re.fullmatch(r"[0-9]+", audience_id):
            raise _ValidationError("audience_id ต้องเป็นตัวเลข")
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        async with LineAdsClient(config) as client:
            data = await client.get(f"/adaccounts/{account_id}/custom-audiences/{audience_id}/upload-job")
        jobs = [{target: row.get(source) for source, target in {
            "audienceGroupJobId": "job_id", "type": "type", "jobStatus": "job_status",
            "audienceCount": "audience_count", "failedType": "failed_type", "created": "created",
        }.items()} for row in data.get("jobs", [])]
        latest = max(jobs, key=_job_order, default={})
        status = latest.get("job_status")
        return ok({"audience_id": audience_id, "jobs": jobs, "latest_status": status,
                   "done": status in {"FINISHED", "FAILED"}})
    except Exception as error:
        return _safe_error(error)
