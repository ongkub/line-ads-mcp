"""Customer-list normalization, privacy, and multipart contracts; no network."""

import hashlib
import json
import re

import httpx
import pytest

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient
from line_ads_mcp.tools import customer_lists as module
from line_ads_mcp.tools.customer_lists import (
    get_customer_list_upload_status,
    normalize_email,
    normalize_ifa,
    normalize_phone,
    upload_customer_list,
)

ENDPOINT = "/adaccounts/A01887296807/custom-audiences/upload"
ORIGINAL_REQUEST = LineAdsClient.request
ORIGINAL_SEND = httpx.AsyncClient.send
PHONE = "0812345678"
NORMAL_PHONE = "66812345678"
HASH = hashlib.sha256(NORMAL_PHONE.encode()).hexdigest()
IFA = "12345678-abcd-4321-abcd-123456789abc"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A01887296807")
    monkeypatch.delenv("LINE_ADS_WORKSPACE_DIR", raising=False)

    async def forbidden(*args, **kwargs):
        pytest.fail("Customer-list tests must never access the network")

    monkeypatch.setattr(LineAdsClient, "request", forbidden)
    monkeypatch.setattr(httpx.AsyncClient, "send", forbidden)


@pytest.fixture
def no_client(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Dry runs and validation errors must not create a client")

    monkeypatch.setattr(LineAdsClient, "__init__", forbidden)


def write_file(tmp_path, text, name="list.txt", encoding="utf-8"):
    path = tmp_path / name
    path.write_text(text, encoding=encoding)
    return str(path)


def assert_private(value, *raw_values):
    text = json.dumps(value, ensure_ascii=False)
    assert not re.search(r"[0-9a-fA-F]{64}", text)
    for raw in raw_values:
        assert raw not in text


@pytest.mark.parametrize("raw,expected", [
    (PHONE, NORMAL_PHONE), ("081-234-5678", NORMAL_PHONE),
    ("+66 81 234 5678", NORMAL_PHONE), ("0066(81)234.5678", NORMAL_PHONE),
    (NORMAL_PHONE, NORMAL_PHONE), ("０８１２３４５６７８", NORMAL_PHONE),
    ("０８１／２３４／５６７８", NORMAL_PHONE), ("0912345678", "66912345678"),
    ("0612345678", "66612345678"), ("02 123 4567", "6621234567"),
    ("053-123-456", "6653123456"), ("071234567", "6671234567"),
    ("+1 (212) 555-1234", "12125551234"), ("00442071234567", "442071234567"),
])
def test_phone_normalization(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("raw", ["081234", "08123456789", "0112345678", "0212345678", "081abc5678", "1234567", "1234567890123456", "++66812345678", "๐๘๑๒๓๔๕๖๗๘"])
def test_invalid_phone(raw):
    with pytest.raises(ValueError):
        normalize_phone(raw)


def test_thai_reason_and_other_default_country():
    with pytest.raises(ValueError, match="เบอร์ไทยผิดรูปแบบ"):
        normalize_phone("08123")
    assert normalize_phone("02071234567", "44") == "442071234567"


@pytest.mark.parametrize("raw,expected", [(" John@GMAIL.com ", "john@gmail.com"), ("ＪＯＨＮ＠ＧＭＡＩＬ．ＣＯＭ", "john@gmail.com"), ("x+y@test.co.th", "x+y@test.co.th")])
def test_email_normalization(raw, expected):
    assert normalize_email(raw) == expected


@pytest.mark.parametrize("raw", ["x", "x@", "@x.com", "a b@x.com", "a@b", "a@b..com", "x" * 115 + "@a.com"])
def test_invalid_email(raw):
    with pytest.raises(ValueError):
        normalize_email(raw)


def test_email_length_boundary():
    assert len(normalize_email("x" * 114 + "@a.com")) == 120


def test_ifa_normalization():
    assert normalize_ifa(" " + IFA.upper() + " ") == IFA
    with pytest.raises(ValueError):
        normalize_ifa(HASH)


async def test_dry_run_counts_masks_and_no_log(tmp_path, no_client, monkeypatch):
    path = write_file(tmp_path, f"{PHONE}\n+66 81 234 5678\n\ninvalid123456789\n08123\n")
    monkeypatch.setenv("LINE_ADS_WORKSPACE_DIR", str(tmp_path))
    result = await upload_customer_list(path, "PHONE", audience_name="customers", workspace_dir=str(tmp_path))
    assert result["ok"] is True
    data = result["data"]
    assert data.items() >= dict(dry_run=True, endpoint=ENDPOINT, id_type="PHONE", api_id_type="HASHED_PHONE_NUMBER", action="ADD", audience="customers", rows_read=5, valid=1, invalid=2, duplicates=1, blank=1, prehashed=0, file_bytes=65, within_size_limit=True, column_used=None).items()
    assert data["invalid_by_reason"] == {"เบอร์โทรต้องเป็นตัวเลข": 1, "เบอร์ไทยผิดรูปแบบ": 1}
    assert [sample["row"] for sample in data["invalid_samples"]] == [4, 5]
    assert_private(result, PHONE, NORMAL_PHONE, "invalid123456789")
    assert not (tmp_path / "line-ads-data").exists()


async def test_invalid_samples_bounded_and_email_mask(tmp_path, no_client):
    path = write_file(tmp_path, "ok@test.com\n" + "john smith@gmail.com\n" * 9)
    data = (await upload_customer_list(path, "EMAIL", audience_name="customers"))["data"]
    assert data["invalid"] == 9
    assert len(data["invalid_samples"]) == 5
    assert data["invalid_samples"][0] == {"row": 2, "masked": "j***@gmail.com", "reason": "อีเมลผิดรูปแบบ"}
    assert_private(data, "john smith@gmail.com", "ok@test.com")


@pytest.mark.parametrize("kind", ["PHONE", "EMAIL"])
async def test_prehashed_passthrough_and_cross_form_dedup(tmp_path, kind, monkeypatch):
    raw = PHONE if kind == "PHONE" else "JOHN@GMAIL.COM"
    normalized = NORMAL_PHONE if kind == "PHONE" else raw.lower()
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    path = write_file(tmp_path, f"{raw}\n{digest.upper()}\n{digest}\n")
    calls = []

    async def request(self, method, endpoint, *, files):
        calls.append(files)
        return {"id": 123, "status": "IN_PROGRESS"}

    monkeypatch.setattr(LineAdsClient, "request", request)
    dry = await upload_customer_list(path, kind, audience_id="123")
    assert dry["data"]["prehashed"] == 2
    assert dry["data"]["valid"] == 1
    assert dry["data"]["duplicates"] == 2
    assert_private(dry, raw, normalized)
    result = await upload_customer_list(path, kind, audience_id="123", dry_run=False)
    assert result["ok"] is True
    assert calls[0]["file"] == ("customer_list.txt", (digest + "\n").encode(), "text/plain")


@pytest.mark.parametrize("header,kind,value", [
    ("phone", "PHONE", PHONE), ("Mobile Number", "PHONE", PHONE),
    ("เบอร์โทรศัพท์", "PHONE", PHONE), ("tel", "PHONE", PHONE),
    ("Email Address", "EMAIL", "a@b.com"), ("อีเมล", "EMAIL", "a@b.com"),
    ("IDFA", "IFA", IFA), ("gaid", "IFA", IFA), ("adid", "IFA", IFA),
])
async def test_csv_auto_column(tmp_path, no_client, header, kind, value):
    path = write_file(tmp_path, f"customer,{header}\nExample,{value}\n", "list.csv")
    result = await upload_customer_list(path, kind, audience_name="customers")
    assert result["ok"] is True
    assert result["data"]["column_used"] == header
    assert result["data"]["rows_read"] == result["data"]["valid"] == 1


async def test_single_column_csv_bom_and_row_numbers(tmp_path, no_client):
    path = write_file(tmp_path, f"contact\n{PHONE}\n\ninvalid\n", "list.csv", "utf-8-sig")
    data = (await upload_customer_list(path, "PHONE", audience_name="customers"))["data"]
    assert data["column_used"] == "contact"
    assert data["rows_read"] == 3
    assert data["blank"] == 1
    assert data["invalid_samples"][0]["row"] == 4


@pytest.mark.parametrize("header", ["phone,mobile", "name,address", "phone,phone"])
async def test_ambiguous_headers_and_explicit_column(tmp_path, no_client, header):
    path = write_file(tmp_path, f"{header}\n{PHONE},{PHONE}\n", "list.csv")
    result = await upload_customer_list(path, "PHONE", audience_name="customers")
    assert result["ok"] is False
    assert all(name in result["message"] for name in header.split(","))
    selected = header.split(",")[1]
    result = await upload_customer_list(path, "PHONE", audience_name="customers", column=selected)
    assert result["ok"] is (header != "phone,phone")


async def test_explicit_column_overrides_detection(tmp_path, no_client):
    path = write_file(tmp_path, f"phone,mobile\ninvalid,{PHONE}\n", "list.csv")
    result = await upload_customer_list(path, "PHONE", audience_name="customers", column="mobile")
    assert result["data"]["valid"] == 1
    result = await upload_customer_list(path, "PHONE", audience_name="customers", column="missing")
    assert result["ok"] is False


async def test_bom_txt_and_ifa_dedup(tmp_path, no_client):
    path = write_file(tmp_path, f"{IFA}\n{IFA.upper()}\n", encoding="utf-8-sig")
    data = (await upload_customer_list(path, "IFA", audience_name="customers"))["data"]
    assert data["valid"] == data["duplicates"] == 1
    assert data["file_bytes"] == 37
    assert data["api_id_type"] == "IFA"
    assert IFA not in json.dumps(data)


@pytest.mark.parametrize("name,message", [("list.xlsx", "CSV"), ("list.pdf", "CSV"), ("missing.txt", "ไม่พบไฟล์")])
async def test_file_errors(tmp_path, no_client, name, message):
    result = await upload_customer_list(str(tmp_path / name), "PHONE", audience_name="customers")
    assert result["ok"] is False
    assert message in result["message"]


async def test_relative_path_empty_invalid_encoding_and_malformed_csv(tmp_path, no_client):
    for text in ("", "invalid\n", "\n\n"):
        result = await upload_customer_list(write_file(tmp_path, text), "PHONE", audience_name="customers")
        assert result["ok"] is False
        assert "valid = 0" in result["message"]
    assert not (await upload_customer_list("list.txt", "PHONE", audience_name="customers"))["ok"]
    path = tmp_path / "bad.txt"
    path.write_bytes(b"\xff" + PHONE.encode())
    result = await upload_customer_list(str(path), "PHONE", audience_name="customers")
    assert not result["ok"]
    assert_private(result, PHONE)
    path = write_file(tmp_path, 'phone\n"unterminated', "bad.csv")
    assert not (await upload_customer_list(path, "PHONE", audience_name="customers"))["ok"]


@pytest.mark.parametrize("arguments", [
    {}, {"audience_name": "x", "audience_id": "123"}, {"audience_name": ""},
    {"audience_name": "x", "action": "REPLACE"}, {"audience_id": ""},
    {"audience_id": "123/456"}, {"audience_name": "x", "action": "REMOVE"},
    {"audience_name": "x", "default_country_code": "+66"},
    {"audience_name": "x", "default_country_code": ""},
    {"audience_name": "x", "column": "phone"},
])
async def test_validation_rules(tmp_path, no_client, arguments):
    path = write_file(tmp_path, PHONE)
    result = await upload_customer_list(path, "PHONE", dry_run=False, **arguments)
    assert result["ok"] is False
    assert result["error_code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("kind", ["HASHED_PHONE_NUMBER", "phone", "INVALID", None, []])
async def test_invalid_id_type(tmp_path, no_client, kind):
    result = await upload_customer_list(write_file(tmp_path, PHONE), kind, audience_name="customers")
    assert result["ok"] is False


@pytest.mark.parametrize("identity,action", [({"audience_name": "customers"}, "ADD"), ({"audience_id": "123"}, "ADD"), ({"audience_id": "123"}, "REPLACE")])
async def test_real_multipart_and_private_change_log(tmp_path, monkeypatch, identity, action):
    path = write_file(tmp_path, f"{PHONE}\n0899999999\n{PHONE}\ninvalid\n")
    calls = []

    async def request(self, method, endpoint, *, files):
        calls.append((method, endpoint, files))
        return {"id": 123, "name": "customers", "status": "IN_PROGRESS", "file": PHONE, "hash": HASH}

    monkeypatch.setattr(LineAdsClient, "request", request)
    result = await upload_customer_list(path, "PHONE", action=action, **identity, dry_run=False, workspace_dir=str(tmp_path))
    assert result["ok"] is True
    assert result["data"]["uploaded"] == 2
    assert result["data"]["id"] == 123
    assert result["data"]["status"] == "IN_PROGRESS"
    assert len(calls) == 1
    method, endpoint, files = calls[0]
    assert (method, endpoint) == ("POST", ENDPOINT)
    key = "name" if "audience_name" in identity else "id"
    assert files[key] == (None, next(iter(identity.values())))
    assert set(files) == {key, "action", "idType", "file"}
    assert files["action"] == (None, action)
    assert files["idType"] == (None, "HASHED_PHONE_NUMBER")
    expected = sorted({HASH, hashlib.sha256(b"66899999999").hexdigest()})
    assert files["file"] == ("customer_list.txt", ("\n".join(expected) + "\n").encode(), "text/plain")
    log = (tmp_path / "line-ads-data/change_log.jsonl").read_text()
    record = json.loads(log)
    assert record["payload"] == {"rows_read": 4, "valid": 2, "invalid": 1, "duplicates": 1, "blank": 0, "prehashed": 0, "file_bytes": 130, "id_type": "PHONE", "action": action, key: next(iter(identity.values()))}
    assert record["entity_id"] == 123
    assert record["after"] is None
    assert_private(result, PHONE, "0899999999", NORMAL_PHONE)
    assert_private(record, PHONE, "0899999999", NORMAL_PHONE)


async def test_real_ifa_sent_without_hash(tmp_path, monkeypatch):
    async def request(self, method, endpoint, *, files):
        assert files["idType"] == (None, "IFA")
        assert files["file"][1] == (IFA + "\n").encode()
        return {"id": 123, "status": "IN_PROGRESS"}

    monkeypatch.setattr(LineAdsClient, "request", request)
    result = await upload_customer_list(write_file(tmp_path, IFA.upper()), "IFA", audience_name="customers", dry_run=False)
    assert result["ok"] is True
    assert IFA not in json.dumps(result)


async def test_size_limit_generated_bytes(tmp_path, no_client, monkeypatch):
    path = write_file(tmp_path, PHONE)
    monkeypatch.setattr(module, "MAX_FILE_BYTES", 64)
    result = await upload_customer_list(path, "PHONE", audience_name="customers", dry_run=False)
    assert result["ok"] is False
    assert "แบ่งไฟล์" in result["message"]
    monkeypatch.setattr(module, "MAX_FILE_BYTES", 65)
    assert (await upload_customer_list(path, "PHONE", audience_name="customers"))["ok"] is True


async def test_server_error_never_echoes_values_in_result_or_log(tmp_path, monkeypatch):
    async def request(*args, **kwargs):
        raise LineAdsAPIError(400, f"bad value {PHONE}: {HASH}", HASH)

    monkeypatch.setattr(LineAdsClient, "request", request)
    result = await upload_customer_list(write_file(tmp_path, PHONE), "PHONE", audience_id="123", dry_run=False, workspace_dir=str(tmp_path))
    assert result["ok"] is False
    assert_private(result, PHONE)
    assert_private(json.loads((tmp_path / "line-ads-data/change_log.jsonl").read_text()), PHONE)


@pytest.mark.parametrize("status_code", [202, 429])
async def test_real_transport_no_retry(tmp_path, monkeypatch, status_code):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(status_code, json={"id": 123, "status": "IN_PROGRESS"})

    original_client = httpx.AsyncClient
    monkeypatch.setattr(httpx.AsyncClient, "send", ORIGINAL_SEND)

    def client(**kwargs):
        return original_client(transport=httpx.MockTransport(respond), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client)
    monkeypatch.setattr(LineAdsClient, "request", ORIGINAL_REQUEST)
    result = await upload_customer_list(write_file(tmp_path, PHONE), "PHONE", audience_name="customers", dry_run=False)
    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert "multipart/form-data; boundary=" in requests[0].headers["content-type"]
    assert PHONE.encode() not in requests[0].content
    assert HASH.encode() in requests[0].content
    assert result["ok"] is (status_code == 202)
    if status_code == 429:
        assert result["status_code"] == 429
        assert result["error_code"] == "RATE_LIMIT"


@pytest.mark.parametrize("status,done", [("QUEUED", False), ("WORKING", False), ("FINISHED", True), ("FAILED", True)])
async def test_upload_status_mapping_latest_by_created(tmp_path, monkeypatch, status, done):
    calls = []

    async def get(self, endpoint):
        calls.append(endpoint)
        return {"jobs": [
            {"audienceGroupId": 123, "audienceGroupJobId": 12, "name": PHONE, "type": "DIFF_REPLACE", "jobStatus": status, "audienceCount": 7, "failedType": None, "created": "2026-10-18T12:00:00Z"},
            {"audienceGroupJobId": 11, "type": "DIFF_ADD", "jobStatus": "FINISHED", "created": "2026-10-17T12:00:00Z"},
        ]}

    monkeypatch.setattr(LineAdsClient, "get", get)
    result = await get_customer_list_upload_status("123", ad_account_id="other")
    assert calls == ["/adaccounts/other/custom-audiences/123/upload-job"]
    assert result["data"]["audience_id"] == "123"
    assert result["data"]["latest_status"] == status
    assert result["data"]["done"] is done
    assert result["data"]["jobs"][0] == {"job_id": 12, "type": "DIFF_REPLACE", "job_status": status, "audience_count": 7, "failed_type": None, "created": "2026-10-18T12:00:00Z"}
    assert_private(result, PHONE)
    assert not (tmp_path / "line-ads-data").exists()


async def test_empty_upload_status(monkeypatch):
    async def get(*args, **kwargs):
        return {"jobs": []}

    monkeypatch.setattr(LineAdsClient, "get", get)
    assert (await get_customer_list_upload_status("123"))["data"] == {"audience_id": "123", "jobs": [], "latest_status": None, "done": False}


@pytest.mark.parametrize("created_a,created_b", [
    ("2026-10-18T12:00:00+07:00", "2026-10-18T06:00:00Z"),
    (9, 10), (None, None),
])
async def test_job_order_timezones_numeric_and_id_tie_break(monkeypatch, created_a, created_b):
    async def get(*args, **kwargs):
        return {"jobs": [
            {"audienceGroupJobId": 9, "jobStatus": "WORKING", "created": created_a},
            {"audienceGroupJobId": 10, "jobStatus": "FINISHED", "created": created_b},
        ]}

    monkeypatch.setattr(LineAdsClient, "get", get)
    result = await get_customer_list_upload_status("123")
    assert result["data"]["latest_status"] == "FINISHED"
    assert result["data"]["done"] is True


@pytest.mark.parametrize("audience_id", ["", "1/2", "1,2", None])
async def test_invalid_status_id_no_client(audience_id, no_client):
    assert not (await get_customer_list_upload_status(audience_id))["ok"]


@pytest.mark.parametrize("raw", ["812345678", "21234567"])
def test_thai_number_missing_leading_zero_from_excel(raw):
    from line_ads_mcp.tools.customer_lists import normalize_phone

    assert normalize_phone(raw) == "66" + raw


@pytest.mark.parametrize("kind,first,second", [
    ("PHONE", PHONE, "0899999999"),
    ("EMAIL", "first@example.com", "second@example.com"),
    ("IFA", IFA, "87654321-abcd-4321-abcd-123456789abc"),
    ("PHONE", HASH, "0899999999"),
])
@pytest.mark.parametrize("multi", [False, True])
async def test_headerless_csv_keeps_first_record_private(tmp_path, no_client, kind, first, second, multi):
    text = f"{first},customer\n{second},other\n" if multi else f"{first}\n{second}\n"
    path = write_file(tmp_path, text, "list.csv")
    result = await upload_customer_list(path, kind, audience_name="customers", column="1" if multi else None)
    assert result["ok"] is True
    assert result["data"]["rows_read"] == result["data"]["valid"] == 2
    assert result["data"]["column_used"] == "column 1"
    assert_private(result, first, second)


async def test_headerless_csv_second_column(tmp_path, no_client):
    path = write_file(tmp_path, f"customer,{PHONE}\nother,0899999999\n", "list.csv")
    result = await upload_customer_list(path, "PHONE", audience_name="customers", column="2")
    assert result["data"]["valid"] == 2
    assert result["data"]["column_used"] == "column 2"
    assert_private(result, PHONE, "0899999999")


@pytest.mark.parametrize("column", [None, "missing", "9"])
async def test_column_errors_redact_identifiers_before_truncation(tmp_path, no_client, column):
    email = "person@example.com"
    cells = [f"  {PHONE}  ", f" {email} ", f" {IFA} ", f" {HASH} ", "x" * 121 + HASH, "label"]
    path = write_file(tmp_path, ",".join(cells) + "\n", "list.csv")
    result = await upload_customer_list(path, "PHONE", audience_name="customers", column=column)
    assert result["ok"] is False
    assert "label" in result["message"]
    for index in range(1, 6):
        assert f"(คอลัมน์ที่ {index})" in result["message"]
    assert_private(result, PHONE, email, IFA)


@pytest.mark.parametrize("header,kind", [
    ("hotel", "PHONE"), ("telegram", "PHONE"), ("โทรสาร", "PHONE"), ("artifact", "IFA"),
])
async def test_headers_match_tokens_not_substrings(tmp_path, no_client, header, kind):
    value = IFA if kind == "IFA" else PHONE
    path = write_file(tmp_path, f"{header},customer\n{value},name\n", "list.csv")
    result = await upload_customer_list(path, kind, audience_name="customers")
    assert result["ok"] is False
    assert "column" in result["message"]


@pytest.mark.parametrize("header,kind,value", [
    ("customer_phone", "PHONE", PHONE), ("telephone", "PHONE", PHONE),
    ("msisdn", "PHONE", PHONE), ("โทรศัพท์ลูกค้า", "PHONE", PHONE),
    ("มือถือ", "PHONE", PHONE), ("หมายเลขเบอร์ลูกค้า", "PHONE", PHONE),
    ("e-mail", "EMAIL", "a@b.com"), ("mail", "EMAIL", "a@b.com"),
])
async def test_exact_header_tokens_and_thai_rules(tmp_path, no_client, header, kind, value):
    path = write_file(tmp_path, f"name,{header}\ncustomer,{value}\n", "list.csv")
    result = await upload_customer_list(path, kind, audience_name="customers")
    assert result["data"]["valid"] == 1
    assert result["data"]["column_used"] == header


@pytest.mark.parametrize("dry_run", [None, 0, "", 1, "false", [], {}])
async def test_dry_run_requires_bool_before_other_validation(tmp_path, no_client, monkeypatch, dry_run):
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid dry_run must be rejected before file preparation")

    monkeypatch.setattr(module, "_prepare", forbidden)
    result = await upload_customer_list("missing", None, dry_run=dry_run)
    assert result["ok"] is False
    assert result["error_code"] == "VALIDATION_ERROR"
    assert "dry_run" in result["message"]


async def test_input_size_checked_before_reading(tmp_path, no_client, monkeypatch):
    path = write_file(tmp_path, PHONE)
    monkeypatch.setattr(module, "MAX_INPUT_BYTES", len(PHONE))
    assert (await upload_customer_list(path, "PHONE", audience_name="customers"))["ok"] is True
    monkeypatch.setattr(module, "MAX_INPUT_BYTES", len(PHONE) - 1)

    def forbidden(*args, **kwargs):
        pytest.fail("Oversized input must not be opened")

    monkeypatch.setattr(module, "_rows", forbidden)
    result = await upload_customer_list(path, "PHONE", audience_name="customers", dry_run=False)
    assert result["error_code"] == "VALIDATION_ERROR"
    assert "200 MB" in result["message"]
    assert_private(result, PHONE)


@pytest.mark.parametrize("name,text", [
    ("list.txt", f"{PHONE}\n\ninvalid\n"),
    ("list.csv", f"phone\n{PHONE}\n\ninvalid\n"),
    ("list.csv", f"{PHONE}\n\ninvalid\n"),
])
async def test_row_limit_counts_blanks_invalid_and_headerless(tmp_path, no_client, monkeypatch, name, text):
    monkeypatch.setattr(module, "MAX_ROWS", 3)
    path = write_file(tmp_path, text, name)
    assert (await upload_customer_list(path, "PHONE", audience_name="customers"))["ok"] is True
    monkeypatch.setattr(module, "MAX_ROWS", 2)
    result = await upload_customer_list(path, "PHONE", audience_name="customers", dry_run=False)
    assert result["error_code"] == "VALIDATION_ERROR"
    assert "จำนวนแถว" in result["message"]
    assert_private(result, PHONE)


@pytest.mark.parametrize("name,text", [
    ("list.txt", PHONE + "\n" + "x" * 21),
    ("list.csv", "phone\n" + PHONE + "\n" + "x" * 21),
    ("list.csv", "phone,note\n" + PHONE + "," + "x" * 21),
    # Each physical line fits, but the quoted cell exceeds the limit.
    ("list.csv", "phone\n" + PHONE + '\n"' + "x" * 10 + '\n' + "x" * 10 + '"\n'),
    ("list.csv", '"' + "x" * 10 + '\n' + "x" * 10 + '"\n' + PHONE),
])
async def test_line_and_cell_length_limits(tmp_path, no_client, monkeypatch, name, text):
    monkeypatch.setattr(module, "MAX_VALUE_CHARS", 20)
    path = write_file(tmp_path, text, name)
    result = await upload_customer_list(path, "PHONE", audience_name="customers", dry_run=False)
    assert result["error_code"] == "VALIDATION_ERROR"
    assert "ค่ายาวผิดปกติ" in result["message"]
    assert_private(result, PHONE, "x" * 21)


@pytest.mark.parametrize("name", ["list.txt", "list.csv"])
async def test_line_length_boundary(tmp_path, no_client, monkeypatch, name):
    monkeypatch.setattr(module, "MAX_VALUE_CHARS", len(PHONE))
    path = write_file(tmp_path, PHONE + "\r\n", name)
    result = await upload_customer_list(path, "PHONE", audience_name="customers")
    assert result["ok"] is True
    assert result["data"]["valid"] == 1


async def test_column_error_change_log_never_contains_raw_cells(tmp_path, no_client):
    email = "private@example.com"
    path = write_file(tmp_path, f" {PHONE} , {email} , {HASH} \n", "list.csv")
    result = await upload_customer_list(path, "PHONE", audience_id="123", dry_run=False,
                                        workspace_dir=str(tmp_path))
    assert result["error_code"] == "VALIDATION_ERROR"
    assert_private(result, PHONE, email)
    record = json.loads((tmp_path / "line-ads-data/change_log.jsonl").read_text())
    assert_private(record, PHONE, email)
