"""Ad and media tools."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient, LineAdsConfig, resolve_ad_account_id

from .common import clean_dict, dry_run_response, handle_tool_error, ok, require_one_of

# Verified from real API data: callToAction is nested {"type": "ADD_FRIEND"} inside creative
CALL_TO_ACTIONS = {"ADD_FRIEND", "LEARN_MORE", "SHOP_NOW", "SIGN_UP", "CONTACT_US", "DOWNLOAD"}
CREATIVE_FORMATS = {"IMAGE", "VIDEO"}
MEDIA_TYPES = {"IMAGE", "VIDEO"}
IMAGE_MIME_TYPES = {"image/jpeg", "image/png"}
VIDEO_MIME_TYPES = {"video/mp4", "video/quicktime"}
AD_TEXT_MAX_LENGTH = 20
IMAGE_MAX_SIZE_BYTES = 10 * 1024 * 1024
VIDEO_MAX_SIZE_BYTES = 1024 * 1024 * 1024


def _validate_ad_text(value: str | None, field_name: str) -> None:
    if value is not None and len(value) > AD_TEXT_MAX_LENGTH:
        raise LineAdsAPIError(
            400,
            f"{field_name} ต้องไม่เกิน {AD_TEXT_MAX_LENGTH} ตัวอักษร",
            "VALIDATION_ERROR",
        )


def _validate_media(file_path: str) -> tuple[Path, str, str]:
    """Returns (path, mime_type, media_type) where media_type is IMAGE or VIDEO."""
    path = Path(file_path)
    if not path.is_absolute():
        raise LineAdsAPIError(400, "file_path ต้องเป็น absolute path", "VALIDATION_ERROR")
    if not path.exists():
        raise LineAdsAPIError(404, f"ไม่พบไฟล์: {file_path}", "FILE_NOT_FOUND")
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    size = path.stat().st_size
    if mime_type in IMAGE_MIME_TYPES:
        if size > IMAGE_MAX_SIZE_BYTES:
            raise LineAdsAPIError(400, "ไฟล์รูปต้องมีขนาดไม่เกิน 10MB", "VALIDATION_ERROR")
        media_type = "IMAGE"
    elif mime_type in VIDEO_MIME_TYPES:
        if size > VIDEO_MAX_SIZE_BYTES:
            raise LineAdsAPIError(400, "ไฟล์วิดีโอต้องมีขนาดไม่เกิน 1GB", "VALIDATION_ERROR")
        media_type = "VIDEO"
    else:
        raise LineAdsAPIError(400, "รองรับเฉพาะ JPG, PNG, MP4, MOV", "VALIDATION_ERROR")
    return path, mime_type, media_type


async def upload_media(
    file_path: str,
    ad_account_id: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Upload image or video. Returns imageHash (used in create_ad).

    Signing: multipart uses content_type="multipart/form-data" (no boundary) with empty body hash.
    Endpoint verified: /adaccounts/{id}/media/upload
    Required fields: file (multipart) + mediaType ("IMAGE" or "VIDEO")
    """
    try:
        path, mime_type, media_type = _validate_media(file_path)
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        endpoint = f"/adaccounts/{account_id}/media/upload"
        payload = {"file_path": str(path), "mime_type": mime_type, "media_type": media_type, "size_bytes": path.stat().st_size}
        if dry_run:
            return dry_run_response("upload_media", endpoint, payload)
        async with LineAdsClient(config) as client:
            with path.open("rb") as fh:
                data = await client.request(
                    "POST",
                    endpoint,
                    files={
                        "file": (path.name, fh, mime_type),
                        "mediaType": (None, media_type),
                    },
                )
        return ok(data)
    except Exception as error:
        return handle_tool_error(error)


async def create_ad(
    adset_id: str,
    name: str,
    image_hash: str,
    title: str,
    call_to_action: str,
    ad_account_id: str | None = None,
    campaign_id: str | None = None,
    creative_format: str = "IMAGE",
    description: str | None = None,
    long_title: str | None = None,
    destination_url: str | None = None,
    small_image_hash: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Create an ad with verified payload structure.

    Verified from real LINE Ads API (inspected from LINE Ads Manager network request):
    - creative is a nested object (not flat fields)
    - image is referenced by imageHash (returned from upload_media), not mediaId
    - title maps to creative.title (not headline)
    - callToAction is a nested object {"type": "ADD_FRIEND"}, not a string
    - For GAIN_FRIENDS campaigns, destination_url is not needed (tied to LINE OA)
    - small_image_hash: smallImageHash inside creative (600×400px for Smart Channel)
      ⚠️ เมื่อใส่ small_image_hash ต้องใส่ long_title ด้วย (LINE Ads บังคับ)
    - campaignId + configuredStatus + smallDelivery ต้องส่งด้วยตาม API spec
    """
    try:
        require_one_of(call_to_action, CALL_TO_ACTIONS, "call_to_action")
        require_one_of(creative_format, CREATIVE_FORMATS, "creative_format")
        _validate_ad_text(title, "title")
        _validate_ad_text(description, "description")
        if small_image_hash and not long_title:
            raise LineAdsAPIError(400, "ต้องระบุ long_title เมื่อใช้ small_image_hash (600×400px) — LINE Ads บังคับ", "VALIDATION_ERROR")
        if destination_url and not destination_url.startswith("https://"):
            raise LineAdsAPIError(400, "destination_url ต้องขึ้นต้นด้วย https://", "VALIDATION_ERROR")
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)

        creative = clean_dict({
            "creativeFormat": creative_format,
            "title": title,
            "description": description,
            "longTitle": long_title,
            "imageHash": image_hash,
            "smallImageHash": small_image_hash,
            "callToAction": {"type": call_to_action},
            "destinationUrl": destination_url,
        })
        payload = clean_dict({
            "campaignId": campaign_id,
            "adgroupId": adset_id,
            "name": name,
            "configuredStatus": "ACTIVE",
            "smallDelivery": False,
            "creative": creative,
        })
        endpoint = f"/adaccounts/{account_id}/ads"
        if dry_run:
            return dry_run_response("create_ad", endpoint, payload)
        async with LineAdsClient(config) as client:
            data = await client.post(endpoint, payload)
        return ok(data)
    except Exception as error:
        return handle_tool_error(error)


async def get_ad_status(ad_id: str, ad_account_id: str | None = None) -> dict[str, Any]:
    try:
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        async with LineAdsClient(config) as client:
            data = await client.get(f"/adaccounts/{account_id}/ads", params={"ids": ad_id})
        if isinstance(data, dict) and isinstance(data.get("datas"), list) and data["datas"]:
            return ok(data["datas"][0])
        return ok(data)
    except Exception as error:
        return handle_tool_error(error)


async def list_ads(adset_id: str, ad_account_id: str | None = None) -> dict[str, Any]:
    try:
        config = LineAdsConfig.from_env()
        account_id = resolve_ad_account_id(ad_account_id, config)
        async with LineAdsClient(config) as client:
            data = await client.get(f"/adaccounts/{account_id}/ads", params={"adgroupId": adset_id})
        return ok(data)
    except Exception as error:
        return handle_tool_error(error)
