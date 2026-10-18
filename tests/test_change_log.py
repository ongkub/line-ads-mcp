"""Best-effort JSONL audit records for every real write tool."""

import asyncio
from datetime import datetime
import json
from pathlib import Path

import pytest

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient
from line_ads_mcp.tools import change_log
from line_ads_mcp.tools.ads import create_ad, pause_ad, resume_ad, upload_media
from line_ads_mcp.tools.adsets import create_adset, pause_adset, resume_adset, update_adset
from line_ads_mcp.tools.campaigns import create_campaign, pause_campaign, resume_campaign, update_campaign

WRITES = [
    (create_campaign, dict(name="โฆษณาทดสอบ", objective="GAIN_FRIENDS", start_date="2026-10-19"), "campaign", None),
    (create_adset, dict(campaign_id="c1", name="โฆษณาทดสอบ", bid_type="CPF", bid_strategy="LOWEST_COST", auto_bid_type="FRIEND", daily_budget=100), "adset", None),
    (create_ad, dict(adset_id="s1", name="โฆษณาทดสอบ", image_hash="hash", title="ทดสอบ", call_to_action="ADD_FRIEND"), "ad", None),
    (update_campaign, dict(campaign_id="c1", daily_budget=150), "campaign", "c1"),
    (update_adset, dict(adset_id="s1", bid_amount=5), "adset", "s1"),
    (pause_campaign, dict(campaign_id="c1"), "campaign", "c1"),
    (resume_campaign, dict(campaign_id="c1"), "campaign", "c1"),
    (pause_adset, dict(adset_id="s1"), "adset", "s1"),
    (resume_adset, dict(adset_id="s1"), "adset", "s1"),
    (pause_ad, dict(ad_id="a1"), "ad", "a1"),
    (resume_ad, dict(ad_id="a1"), "ad", "a1"),
    (upload_media, {}, "media", None),
]


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A123")
    monkeypatch.delenv("LINE_ADS_WORKSPACE_DIR", raising=False)


def media_arguments(tool, arguments, root):
    arguments = dict(arguments)
    if tool is upload_media:
        image = root / "รูป.png"
        image.write_bytes(b"image")
        arguments["file_path"] = str(image)
    return arguments


def mock_api(monkeypatch, fail=False):
    state = {"body": {}, "written": False}

    async def get(self, path, params=None):
        row = {"id": params["ids"], "configuredStatus": "PAUSED", "deliveryStatus": "NOT_DELIVERING"}
        if state["written"]:
            row.update(state["body"])
        return {"datas": [row]}

    async def post(self, path, body):
        if fail:
            raise LineAdsAPIError(400, "เขียนไม่สำเร็จ", "REJECTED")
        state.update(body=body, written=True)
        return {"id": "new1"}

    async def request(self, method, path, **kwargs):
        assert method == "POST"
        assert kwargs["files"]["mediaType"] == (None, "IMAGE")
        if fail:
            raise LineAdsAPIError(400, "เขียนไม่สำเร็จ", "REJECTED")
        return {"imageHash": "media-hash"}

    monkeypatch.setattr(LineAdsClient, "get", get)
    monkeypatch.setattr(LineAdsClient, "post", post)
    monkeypatch.setattr(LineAdsClient, "request", request)


def read_records(root):
    return [json.loads(line) for line in (root / "line-ads-data" / "change_log.jsonl").read_text(encoding="utf-8").splitlines()]


@pytest.mark.parametrize("tool,arguments,entity_type,entity_id", WRITES)
@pytest.mark.parametrize("fail", [False, True])
async def test_all_real_writes_log_once(monkeypatch, tmp_path, tool, arguments, entity_type, entity_id, fail):
    mock_api(monkeypatch, fail)
    arguments = media_arguments(tool, arguments, tmp_path)
    result = await tool(**arguments, dry_run=False, workspace_dir=str(tmp_path))
    assert result["ok"] is (not fail)
    assert result["change_log"] == str(tmp_path / "line-ads-data" / "change_log.jsonl")
    records = read_records(tmp_path)
    assert len(records) == 1
    record = records[0]
    assert set(record) == {"ts", "tool", "ad_account_id", "entity_type", "entity_id", "endpoint", "payload", "before", "after", "readback_ok", "ok", "error"}
    assert datetime.fromisoformat(record["ts"]).utcoffset().total_seconds() == 0
    assert record["tool"] == tool.__name__
    assert record["ad_account_id"] == "A123"
    assert record["entity_type"] == entity_type
    assert record["entity_id"] == (entity_id if entity_id is not None else ("new1" if not fail and tool is not upload_media else None))
    assert record["endpoint"].startswith("/adaccounts/A123/")
    assert record["payload"]
    assert record["ok"] is result["ok"]
    if fail:
        assert (record["before"] is not None) == (entity_id is not None)
    else:
        assert record["before"] == result.get("before")
    if fail:
        assert record["error"]["error_code"] == "REJECTED"
        assert record["after"] is None
    else:
        assert record["error"] is None
        assert record["after"] == result.get("readback")
        assert record["readback_ok"] == result.get("readback_ok")


@pytest.mark.parametrize("tool,arguments,entity_type,entity_id", WRITES)
async def test_dry_runs_never_log_or_create_client(monkeypatch, tmp_path, tool, arguments, entity_type, entity_id):
    arguments = media_arguments(tool, arguments, tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail("dry runs must not create a client or call append_change")

    monkeypatch.setattr(LineAdsClient, "__init__", forbidden)
    monkeypatch.setattr(change_log, "append_change", forbidden)
    result = await tool(**arguments, workspace_dir=str(tmp_path))
    assert result["dry_run"] is True
    assert "change_log" not in result
    assert not (tmp_path / "line-ads-data").exists()


async def test_append_preserves_thai_and_one_line_per_write(monkeypatch, tmp_path):
    mock_api(monkeypatch)
    for _ in range(2):
        result = await create_campaign(name="โฆษณาทดสอบ", objective="GAIN_FRIENDS", start_date="2026-10-19", dry_run=False, workspace_dir=str(tmp_path))
        assert result["ok"]
    content = (tmp_path / "line-ads-data" / "change_log.jsonl").read_text(encoding="utf-8")
    assert "โฆษณาทดสอบ" in content
    assert len(content.splitlines()) == 2


@pytest.mark.parametrize("directory", ["relative", "missing", "file", "empty", "io_error", "no_dir", "env"])
async def test_workspace_handling_does_not_change_api_result(monkeypatch, tmp_path, directory):
    mock_api(monkeypatch)
    kwargs = {}
    if directory == "relative":
        kwargs["workspace_dir"] = "relative/path"
    elif directory == "missing":
        kwargs["workspace_dir"] = str(tmp_path / "missing")
    elif directory == "file":
        path = tmp_path / "file"
        path.write_text("file")
        kwargs["workspace_dir"] = str(path)
    elif directory == "empty":
        kwargs["workspace_dir"] = ""
    elif directory == "io_error":
        kwargs["workspace_dir"] = str(tmp_path)
        (tmp_path / "line-ads-data").write_text("blocks mkdir")
    elif directory == "env":
        monkeypatch.setenv("LINE_ADS_WORKSPACE_DIR", str(tmp_path))
    result = await create_campaign(name="ทดสอบ", objective="GAIN_FRIENDS", start_date="2026-10-19", dry_run=False, **kwargs)
    assert result["ok"] is True
    assert result["data"] == {"id": "new1"}
    assert result["readback_ok"] is True
    if directory == "no_dir":
        assert result["change_log"] == "skipped (no workspace_dir)"
        assert not (tmp_path / "line-ads-data").exists()
    elif directory == "env":
        assert len(read_records(tmp_path)) == 1
    else:
        assert result["change_log_error"]
        if directory == "missing":
            assert not (tmp_path / "missing").exists()


async def test_explicit_workspace_overrides_env(monkeypatch, tmp_path):
    mock_api(monkeypatch)
    monkeypatch.setenv("LINE_ADS_WORKSPACE_DIR", str(tmp_path / "missing"))
    result = await pause_ad("a1", dry_run=False, workspace_dir=str(tmp_path))
    assert "change_log_error" not in result
    assert read_records(tmp_path)[0]["tool"] == "pause_ad"


async def test_prewrite_failure_logged(monkeypatch, tmp_path):
    mock_api(monkeypatch)

    async def get(self, path, params=None):
        return {"datas": []}

    monkeypatch.setattr(LineAdsClient, "get", get)
    result = await pause_adset("missing", dry_run=False, workspace_dir=str(tmp_path))
    assert result["error_code"] == "NOT_FOUND"
    record = read_records(tmp_path)[0]
    assert record["before"] is None
    assert record["after"] is None
    assert record["error"]["error_code"] == "NOT_FOUND"


async def test_validation_failure_logged_without_api_call(tmp_path):
    result = await create_campaign(name="ทดสอบ", objective="GAIN_FRIENDS", status="DRAFT", dry_run=False, workspace_dir=str(tmp_path))
    assert result["error_code"] == "VALIDATION_ERROR"
    record = read_records(tmp_path)[0]
    assert record["ok"] is False
    assert record["error"]["error_code"] == "VALIDATION_ERROR"


async def test_readback_failure_logged_as_successful_write(monkeypatch, tmp_path):
    mock_api(monkeypatch)

    async def get(self, path, params=None):
        raise RuntimeError("cannot read back")

    monkeypatch.setattr(LineAdsClient, "get", get)
    result = await create_campaign(name="ทดสอบ", objective="GAIN_FRIENDS", start_date="2026-10-19", dry_run=False, workspace_dir=str(tmp_path))
    assert result["ok"] is True
    assert result["readback_ok"] is None
    record = read_records(tmp_path)[0]
    assert record["ok"] is True
    assert record["error"] is None
    assert record["readback_ok"] is None


async def test_concurrent_records_stay_independent(monkeypatch, tmp_path):
    async def get(self, path, params=None):
        await asyncio.sleep(0)
        return {"datas": [{"id": params["ids"], "configuredStatus": "PAUSED"}]}

    async def post(self, path, body):
        await asyncio.sleep(0)
        return {}

    monkeypatch.setattr(LineAdsClient, "get", get)
    monkeypatch.setattr(LineAdsClient, "post", post)
    await asyncio.gather(pause_campaign("c1", dry_run=False, workspace_dir=str(tmp_path)), pause_ad("a1", dry_run=False, workspace_dir=str(tmp_path)))
    records = read_records(tmp_path)
    assert {(r["tool"], r["entity_id"]) for r in records} == {("pause_campaign", "c1"), ("pause_ad", "a1")}


def test_append_uses_single_write_call(monkeypatch, tmp_path):
    writes = []

    class Stream:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def write(self, value):
            writes.append(value)

    def open_stream(self, mode, encoding):
        assert mode == "a"
        assert encoding == "utf-8"
        return Stream()

    monkeypatch.setattr(Path, "open", open_stream)
    path = change_log.append_change(str(tmp_path), {"payload": "ภาษาไทย\nหนึ่งระเบียน"})
    assert path == str(tmp_path / "line-ads-data" / "change_log.jsonl")
    assert len(writes) == 1
    assert len(writes[0].splitlines()) == 1
    assert json.loads(writes[0])["payload"] == "ภาษาไทย\nหนึ่งระเบียน"
