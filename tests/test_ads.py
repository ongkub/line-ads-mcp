"""Tests for ad and media tools — payload verified against real LINE Ads API v3."""

import pytest

from line_ads_mcp.tools.ads import create_ad, upload_media


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A01887296807")


# ---------------------------------------------------------------------------
# create_ad
# ---------------------------------------------------------------------------

IMAGE_HASH = "0h2g_cCjKobUhiGnLRi7gSHzNKZjlRd3pLAmJwdUZSYSRLdEJFKjdcWyBTYxEkaVFBInRycTcZSCcvIkFsNXxDSzBZYCQ7KEIdPn1dWz9RTw0_dnp7Xzo"


@pytest.mark.asyncio
async def test_create_ad_defaults_to_dry_run():
    result = await create_ad(
        adset_id="1752193645380",
        name="Test Ad",
        image_hash=IMAGE_HASH,
        title="Test Title",
        call_to_action="ADD_FRIEND",
    )

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["endpoint"] == "/adaccounts/A01887296807/ads"


@pytest.mark.asyncio
async def test_create_ad_creative_is_nested_object():
    """Verified: creative must be a nested object, not flat fields."""
    result = await create_ad(
        adset_id="1752193645380",
        name="Test Ad",
        image_hash=IMAGE_HASH,
        title="Test Title",
        call_to_action="ADD_FRIEND",
        description="Test Description",
    )

    payload = result["payload"]
    assert "creative" in payload
    creative = payload["creative"]
    assert creative["imageHash"] == IMAGE_HASH
    assert creative["title"] == "Test Title"
    assert creative["description"] == "Test Description"
    assert creative["creativeFormat"] == "IMAGE"
    # callToAction is a nested object, not a string
    assert creative["callToAction"] == {"type": "ADD_FRIEND"}
    # Old flat fields must NOT appear at top level
    assert "mediaId" not in payload
    assert "headline" not in payload
    assert "callToAction" not in payload


@pytest.mark.asyncio
async def test_create_ad_no_destinationUrl_for_gain_friends():
    """GAIN_FRIENDS campaigns don't need destinationUrl."""
    result = await create_ad(
        adset_id="1752193645380",
        name="Test Ad",
        image_hash=IMAGE_HASH,
        title="Title",
        call_to_action="ADD_FRIEND",
    )

    creative = result["payload"]["creative"]
    assert "destinationUrl" not in creative


@pytest.mark.asyncio
async def test_create_ad_destination_url_in_creative():
    result = await create_ad(
        adset_id="1752193645380",
        name="Test Ad",
        image_hash=IMAGE_HASH,
        title="Title",
        call_to_action="LEARN_MORE",
        destination_url="https://example.com",
    )

    assert result["payload"]["creative"]["destinationUrl"] == "https://example.com"


@pytest.mark.asyncio
async def test_create_ad_rejects_http_destination_url():
    result = await create_ad(
        adset_id="1752193645380",
        name="Test Ad",
        image_hash=IMAGE_HASH,
        title="Title",
        call_to_action="LEARN_MORE",
        destination_url="http://example.com",
    )

    assert result["ok"] is False
    assert "https" in result["message"]


@pytest.mark.asyncio
async def test_create_ad_rejects_invalid_call_to_action():
    result = await create_ad(
        adset_id="1752193645380",
        name="Test Ad",
        image_hash=IMAGE_HASH,
        title="Title",
        call_to_action="BUY_NOW",
    )

    assert result["ok"] is False
    assert "call_to_action" in result["message"]


@pytest.mark.asyncio
async def test_create_ad_accepts_add_friend_cta():
    """ADD_FRIEND is the correct CTA for GAIN_FRIENDS campaigns — was missing before."""
    result = await create_ad(
        adset_id="1752193645380",
        name="Test Ad",
        image_hash=IMAGE_HASH,
        title="Title",
        call_to_action="ADD_FRIEND",
    )

    assert result["ok"] is True
    assert result["payload"]["creative"]["callToAction"]["type"] == "ADD_FRIEND"


@pytest.mark.asyncio
async def test_create_ad_rejects_title_over_20_chars():
    result = await create_ad(
        adset_id="1752193645380",
        name="Test Ad",
        image_hash=IMAGE_HASH,
        title="ขายออนไลน์ โตด้วยแผนที่ชัด",
        call_to_action="ADD_FRIEND",
    )

    assert result["ok"] is False
    assert "title" in result["message"]
    assert "20" in result["message"]


@pytest.mark.asyncio
async def test_create_ad_rejects_description_over_20_chars():
    result = await create_ad(
        adset_id="1752193645380",
        name="Test Ad",
        image_hash=IMAGE_HASH,
        title="Title",
        description="ให้ทีม Agency ช่วยวางแผนยิงแอด",
        call_to_action="ADD_FRIEND",
    )

    assert result["ok"] is False
    assert "description" in result["message"]
    assert "20" in result["message"]


# ---------------------------------------------------------------------------
# upload_media
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_media_dry_run_shows_correct_endpoint(tmp_path):
    """Endpoint verified: /media/upload (not /images or /videos)."""
    img = tmp_path / "test.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    result = await upload_media(str(img), dry_run=True)

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["endpoint"] == "/adaccounts/A01887296807/media/upload"


@pytest.mark.asyncio
async def test_upload_media_dry_run_payload_includes_media_type(tmp_path):
    """mediaType field is required by API — verified from real 400 error."""
    img = tmp_path / "test.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)

    result = await upload_media(str(img), dry_run=True)

    assert result["payload"]["media_type"] == "IMAGE"


@pytest.mark.asyncio
async def test_upload_media_rejects_non_absolute_path():
    result = await upload_media("relative/path.png", dry_run=True)

    assert result["ok"] is False
    assert "absolute" in result["message"]


@pytest.mark.asyncio
async def test_upload_media_rejects_missing_file():
    result = await upload_media("/tmp/does_not_exist_12345.png", dry_run=True)

    assert result["ok"] is False


@pytest.mark.asyncio
async def test_upload_video_dry_run_media_type(tmp_path):
    vid = tmp_path / "clip.mp4"
    vid.write_bytes(b"\x00\x00\x00\x18ftyp" + b"\x00" * 50)

    result = await upload_media(str(vid), dry_run=True)

    assert result["ok"] is True
    assert result["payload"]["media_type"] == "VIDEO"
