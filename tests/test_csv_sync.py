"""Tests for sync_ad_daily_csv tool."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
import pytest

from line_ads_mcp.tools import csv_sync
from line_ads_mcp.tools.csv_sync import CSV_HEADERS, RUN_LOG_HEADERS, sync_ad_daily_csv


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A01887296807")


def _fake_report_response(rows: list[dict[str, Any]], complete: bool = True, reason: str | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "data": {
            "report_level": "AD",
            "date_range": {"start": "2026-05-01", "end": "2026-05-02"},
            "data": rows,
            "paging": {
                "pages_fetched": 1,
                "total_elements": len(rows),
                "rows": len(rows),
                "complete": complete,
                "reason": reason,
            },
            "by_day": True,
        },
    }


@pytest.mark.asyncio
async def test_header_exact(tmp_path, monkeypatch):
    """Header must match the exact CSV contract."""
    rows = [
        {
            "date": "2026-05-01",
            "campaign": {"id": "c1", "name": "Camp1", "objective": "WEBSITE_TRAFFIC"},
            "adgroup": {"id": "ag1", "name": "Group1"},
            "ad": {"id": "ad1", "name": "Ad1"},
            "statistics": {"imp": 100, "click": 10, "cost": 50.0, "cv": 2},
        }
    ]

    async def fake_get_report(*args, **kwargs):
        return _fake_report_response(rows)

    monkeypatch.setattr(csv_sync, "get_report", fake_get_report)

    res = await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)
    assert res["ok"] is True

    csv_path = tmp_path / "line-ads-data" / "ad_daily.csv"
    assert csv_path.exists()

    with open(csv_path, "r", encoding="utf-8") as f:
        first_line = f.readline().rstrip("\r\n")

    expected_header = ",".join(CSV_HEADERS)
    assert first_line == expected_header
    assert first_line == (
        "date,account_timezone,campaign_id,campaign_name,objective,adgroup_id,adgroup_name,"
        "ad_id,ad_name,impressions,clicks,spend,currency,results,result_type,pulled_at"
    )


@pytest.mark.asyncio
async def test_first_run_inserts(tmp_path, monkeypatch):
    """First run inserts all valid rows, updating total and preview."""
    rows = [
        {
            "date": "2026-05-01",
            "campaign": {"id": "c1", "name": "Camp1", "objective": "WEBSITE_TRAFFIC"},
            "adgroup": {"id": "ag1", "name": "Group1"},
            "ad": {"id": "ad1", "name": "Ad1"},
            "statistics": {"imp": 100, "click": 10, "cost": 50.0, "cv": 2},
        },
        {
            "date": "2026-05-01",
            "campaign": {"id": "c1", "name": "Camp1", "objective": "WEBSITE_TRAFFIC"},
            "adgroup": {"id": "ag1", "name": "Group1"},
            "ad": {"id": "ad2", "name": "Ad2"},
            "statistics": {"imp": 200, "click": 20, "cost": 100.0, "cv": 4},
        },
    ]

    async def fake_get_report(*args, **kwargs):
        return _fake_report_response(rows)

    monkeypatch.setattr(csv_sync, "get_report", fake_get_report)

    res = await sync_ad_daily_csv(
        "2026-05-01",
        "2026-05-01",
        str(tmp_path),
        account_timezone="Asia/Bangkok",
        currency="THB",
        dry_run=False,
    )

    assert res["ok"] is True
    data = res["data"]
    assert data["inserted"] == 2
    assert data["replaced"] == 0
    assert data["unchanged"] == 0
    assert data["rejected"] == 0
    assert data["rows_total"] == 2
    assert data["data_complete"] is True
    assert len(data["preview"]) == 2

    csv_path = tmp_path / "line-ads-data" / "ad_daily.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 2
        assert reader[0]["ad_id"] == "ad1"
        assert reader[0]["account_timezone"] == "Asia/Bangkok"
        assert reader[0]["currency"] == "THB"
        assert reader[1]["ad_id"] == "ad2"

    run_log_path = tmp_path / "line-ads-data" / "run_log.csv"
    with open(run_log_path, "r", encoding="utf-8") as f:
        log_rows = list(csv.DictReader(f))
        assert len(log_rows) == 1
        assert log_rows[0]["status"] == "ok"
        assert int(log_rows[0]["rows_written"]) == 2


@pytest.mark.asyncio
async def test_rerun_same_data_no_duplicates(tmp_path, monkeypatch):
    """Rerun with same data results in 0 inserted, all unchanged, no duplicates."""
    rows = [
        {
            "date": "2026-05-01",
            "campaign": {"id": "c1", "name": "Camp1", "objective": "WEBSITE_TRAFFIC"},
            "adgroup": {"id": "ag1", "name": "Group1"},
            "ad": {"id": "ad1", "name": "Ad1"},
            "statistics": {"imp": 100, "click": 10, "cost": 50.0, "cv": 2},
        }
    ]

    async def fake_get_report(*args, **kwargs):
        return _fake_report_response(rows)

    monkeypatch.setattr(csv_sync, "get_report", fake_get_report)

    # First run
    await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)

    # Second run (same data)
    res = await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)
    assert res["ok"] is True
    data = res["data"]
    assert data["inserted"] == 0
    assert data["replaced"] == 0
    assert data["unchanged"] == 1
    assert data["rows_total"] == 1

    csv_path = tmp_path / "line-ads-data" / "ad_daily.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 1


@pytest.mark.asyncio
async def test_corrected_value_replaces_old_row(tmp_path, monkeypatch):
    """Updated metric values replace the existing row rather than duplicate."""
    initial_rows = [
        {
            "date": "2026-05-01",
            "campaign": {"id": "c1", "name": "Camp1", "objective": "WEBSITE_TRAFFIC"},
            "adgroup": {"id": "ag1", "name": "Group1"},
            "ad": {"id": "ad1", "name": "Ad1"},
            "statistics": {"imp": 100, "click": 10, "cost": 50.0, "cv": 2},
        }
    ]
    corrected_rows = [
        {
            "date": "2026-05-01",
            "campaign": {"id": "c1", "name": "Camp1", "objective": "WEBSITE_TRAFFIC"},
            "adgroup": {"id": "ag1", "name": "Group1"},
            "ad": {"id": "ad1", "name": "Ad1"},
            "statistics": {"imp": 150, "click": 15, "cost": 75.0, "cv": 3},
        }
    ]

    async def fake_initial(*args, **kwargs):
        return _fake_report_response(initial_rows)

    async def fake_corrected(*args, **kwargs):
        return _fake_report_response(corrected_rows)

    monkeypatch.setattr(csv_sync, "get_report", fake_initial)
    await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)

    monkeypatch.setattr(csv_sync, "get_report", fake_corrected)
    res = await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)

    assert res["ok"] is True
    data = res["data"]
    assert data["inserted"] == 0
    assert data["replaced"] == 1
    assert data["unchanged"] == 0
    assert data["rows_total"] == 1

    csv_path = tmp_path / "line-ads-data" / "ad_daily.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 1
        assert reader[0]["impressions"] == "150"
        assert reader[0]["clicks"] == "15"
        assert reader[0]["spend"] == "75.0"
        assert reader[0]["results"] == "3"


@pytest.mark.asyncio
async def test_other_dates_kept(tmp_path, monkeypatch):
    """Upsert keeps rows for other dates and outputs sorted by date then ad_id."""
    day1_rows = [
        {
            "date": "2026-05-01",
            "campaign": {"id": "c1", "name": "Camp1"},
            "ad": {"id": "ad_b", "name": "Ad B"},
            "imp": 100,
            "click": 5,
        }
    ]
    day2_rows = [
        {
            "date": "2026-05-02",
            "campaign": {"id": "c1", "name": "Camp1"},
            "ad": {"id": "ad_a", "name": "Ad A"},
            "imp": 200,
            "click": 10,
        }
    ]

    async def fake_day1(*args, **kwargs):
        return _fake_report_response(day1_rows)

    async def fake_day2(*args, **kwargs):
        return _fake_report_response(day2_rows)

    monkeypatch.setattr(csv_sync, "get_report", fake_day1)
    await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)

    monkeypatch.setattr(csv_sync, "get_report", fake_day2)
    res = await sync_ad_daily_csv("2026-05-02", "2026-05-02", str(tmp_path), dry_run=False)

    assert res["ok"] is True
    data = res["data"]
    assert data["inserted"] == 1
    assert data["rows_total"] == 2

    csv_path = tmp_path / "line-ads-data" / "ad_daily.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 2
        # sorted by date then ad_id
        assert reader[0]["date"] == "2026-05-01"
        assert reader[0]["ad_id"] == "ad_b"
        assert reader[1]["date"] == "2026-05-02"
        assert reader[1]["ad_id"] == "ad_a"


@pytest.mark.asyncio
async def test_rows_missing_ad_id_rejected(tmp_path, monkeypatch):
    """Rows missing date or ad_id are rejected (counted, not written)."""
    rows = [
        {
            "date": "2026-05-01",
            "ad": {"id": "ad1", "name": "Valid Ad"},
            "imp": 10,
        },
        {
            "date": "2026-05-01",
            # missing ad and adId
            "imp": 20,
        },
        {
            # missing date
            "ad": {"id": "ad3", "name": "No Date Ad"},
            "imp": 30,
        },
    ]

    async def fake_get_report(*args, **kwargs):
        return _fake_report_response(rows)

    monkeypatch.setattr(csv_sync, "get_report", fake_get_report)

    res = await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)
    assert res["ok"] is True
    data = res["data"]
    assert data["inserted"] == 1
    assert data["rejected"] == 2
    assert data["rows_total"] == 1

    csv_path = tmp_path / "line-ads-data" / "ad_daily.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 1
        assert reader[0]["ad_id"] == "ad1"


@pytest.mark.asyncio
async def test_gain_friends_results_equals_click(tmp_path, monkeypatch):
    """GAIN_FRIENDS results = click, result_type = friends(click). Other objectives use cv."""
    rows = [
        {
            "date": "2026-05-01",
            "campaign": {"id": "c1", "objective": "GAIN_FRIENDS"},
            "ad": {"id": "ad_gf"},
            "click": 42,
            "cv": 0,
        },
        {
            "date": "2026-05-01",
            "campaign": {"id": "c2", "objective": "CONVERSIONS"},
            "ad": {"id": "ad_conv"},
            "click": 42,
            "cv": 5,
        },
    ]

    async def fake_get_report(*args, **kwargs):
        return _fake_report_response(rows)

    monkeypatch.setattr(csv_sync, "get_report", fake_get_report)

    res = await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)
    assert res["ok"] is True

    csv_path = tmp_path / "line-ads-data" / "ad_daily.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 2
        # ad_conv
        assert reader[0]["ad_id"] == "ad_conv"
        assert reader[0]["results"] == "5"
        assert reader[0]["result_type"] == "cv"
        # ad_gf
        assert reader[1]["ad_id"] == "ad_gf"
        assert reader[1]["results"] == "42"
        assert reader[1]["result_type"] == "friends(click)"


@pytest.mark.asyncio
async def test_missing_metric_empty_not_zero(tmp_path, monkeypatch):
    """Missing metric from API is represented as empty string, never 0."""
    rows = [
        {
            "date": "2026-05-01",
            "ad": {"id": "ad_missing"},
            "imp": 0,  # 0 is present
            # click, cost, cv are absent
        }
    ]

    async def fake_get_report(*args, **kwargs):
        return _fake_report_response(rows)

    monkeypatch.setattr(csv_sync, "get_report", fake_get_report)

    res = await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)
    assert res["ok"] is True

    csv_path = tmp_path / "line-ads-data" / "ad_daily.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 1
        assert reader[0]["impressions"] == "0"
        assert reader[0]["clicks"] == ""
        assert reader[0]["spend"] == ""
        assert reader[0]["results"] == ""
        assert reader[0]["result_type"] == ""


@pytest.mark.asyncio
async def test_thai_names_with_commas_quotes_roundtrip(tmp_path, monkeypatch):
    """Thai names with commas and quotes round-trip through CSV without corruption."""
    complex_ad_name = 'โฆษณา "พิเศษสุด", แคมเปญ \'สุดคุ้ม\''
    complex_camp_name = 'แคมเปญ 1, "ลด 50%"'

    rows = [
        {
            "date": "2026-05-01",
            "campaign": {"id": "c1", "name": complex_camp_name},
            "ad": {"id": "ad_thai", "name": complex_ad_name},
            "imp": 50,
        }
    ]

    async def fake_get_report(*args, **kwargs):
        return _fake_report_response(rows)

    monkeypatch.setattr(csv_sync, "get_report", fake_get_report)

    res = await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)
    assert res["ok"] is True

    csv_path = tmp_path / "line-ads-data" / "ad_daily.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 1
        assert reader[0]["ad_name"] == complex_ad_name
        assert reader[0]["campaign_name"] == complex_camp_name


@pytest.mark.asyncio
async def test_incomplete_report_csv_untouched_and_run_log_incomplete(tmp_path, monkeypatch):
    """If paging.complete is False, ad_daily.csv is untouched and run_log is logged as incomplete."""
    initial_rows = [
        {
            "date": "2026-05-01",
            "ad": {"id": "ad1", "name": "Ad1"},
            "imp": 100,
        }
    ]

    async def fake_ok(*args, **kwargs):
        return _fake_report_response(initial_rows, complete=True)

    monkeypatch.setattr(csv_sync, "get_report", fake_ok)
    await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)

    csv_path = tmp_path / "line-ads-data" / "ad_daily.csv"
    initial_mtime = csv_path.stat().st_mtime_ns

    # Now simulate incomplete report
    incomplete_rows = [
        {
            "date": "2026-05-01",
            "ad": {"id": "ad1", "name": "Ad1 Updated"},
            "imp": 999,
        }
    ]

    async def fake_incomplete(*args, **kwargs):
        return _fake_report_response(incomplete_rows, complete=False, reason="PAGE_LIMIT_REACHED")

    monkeypatch.setattr(csv_sync, "get_report", fake_incomplete)
    res = await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)

    assert res["ok"] is True
    data = res["data"]
    assert data["data_complete"] is False

    # ad_daily.csv must be untouched
    assert csv_path.stat().st_mtime_ns == initial_mtime
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 1
        assert reader[0]["impressions"] == "100"

    # run_log.csv has new row with incomplete status
    run_log_path = tmp_path / "line-ads-data" / "run_log.csv"
    with open(run_log_path, "r", encoding="utf-8") as f:
        log_rows = list(csv.DictReader(f))
        assert len(log_rows) == 2
        assert log_rows[1]["status"] == "incomplete"
        assert int(log_rows[1]["rows_written"]) == 0
        assert "PAGE_LIMIT_REACHED" in log_rows[1]["note"]


@pytest.mark.asyncio
async def test_dry_run_writes_nothing(tmp_path, monkeypatch):
    """dry_run=True returns preview and counts, writes nothing to disk."""
    rows = [
        {
            "date": "2026-05-01",
            "ad": {"id": "ad1", "name": "Ad1"},
            "imp": 100,
        }
    ]

    async def fake_get_report(*args, **kwargs):
        return _fake_report_response(rows)

    monkeypatch.setattr(csv_sync, "get_report", fake_get_report)

    res = await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=True)
    assert res["ok"] is True
    data = res["data"]
    assert data["dry_run"] is True
    assert data["inserted"] == 1
    assert data["rows_total"] == 1
    assert len(data["preview"]) == 1

    # Directory line-ads-data must not exist
    assert not (tmp_path / "line-ads-data").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_dir", ["relative/path", "", None, "/non/existent/path/for/sure"])
async def test_relative_or_missing_workspace_dir_error(tmp_path, invalid_dir):
    """Relative, missing, or non-existent workspace_dir returns validation error."""
    path = invalid_dir
    if invalid_dir == "/non/existent/path/for/sure":
        path = str(tmp_path / "does_not_exist")

    res = await sync_ad_daily_csv("2026-05-01", "2026-05-01", workspace_dir=path)
    assert res["ok"] is False
    assert res["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_atomic_write_leaves_no_temp_file(tmp_path, monkeypatch):
    """Atomic write leaves no temporary files on success or failure."""
    rows = [
        {
            "date": "2026-05-01",
            "ad": {"id": "ad1", "name": "Ad1"},
            "imp": 100,
        }
    ]

    async def fake_get_report(*args, **kwargs):
        return _fake_report_response(rows)

    monkeypatch.setattr(csv_sync, "get_report", fake_get_report)

    # Success case
    res = await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)
    assert res["ok"] is True
    data_dir = tmp_path / "line-ads-data"
    assert list(data_dir.glob("*.tmp")) == []

    # Failure during write: monkeypatch csv.DictWriter.writerow to raise error
    def broken_writerow(*args, **kwargs):
        raise OSError("Simulated disk error during write")

    monkeypatch.setattr(csv.DictWriter, "writerow", broken_writerow)

    res_fail = await sync_ad_daily_csv("2026-05-01", "2026-05-01", str(tmp_path), dry_run=False)
    assert res_fail["ok"] is False
    # Verify no temp files left
    assert list(data_dir.glob("*.tmp")) == []
