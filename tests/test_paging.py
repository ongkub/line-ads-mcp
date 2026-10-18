"""Tests for paging helper fetch_all_pages."""

import pytest

from line_ads_mcp.client import LineAdsClient, LineAdsConfig
from line_ads_mcp.tools.paging import fetch_all_pages


class MockClient:
    def __init__(self, responses: list[dict]):
        self.responses = list(responses)
        self.calls: list[tuple[str, dict]] = []

    async def get(self, path: str, params: dict | None = None):
        self.calls.append((path, dict(params or {})))
        if self.responses:
            return self.responses.pop(0)
        return {"datas": []}


@pytest.mark.asyncio
async def test_fetch_all_pages_multi_page_until_total_elements():
    """Multi-page fetching collects until totalElements is reached."""
    page1 = {
        "paging": {"page": 1, "size": 100, "totalElements": 150},
        "datas": [{"id": i} for i in range(100)],
    }
    page2 = {
        "paging": {"page": 2, "size": 100, "totalElements": 150},
        "datas": [{"id": i} for i in range(100, 150)],
    }
    client = MockClient([page1, page2])

    result = await fetch_all_pages(client, "/endpoint", page_size=100)

    assert len(result["datas"]) == 150
    assert result["paging"]["pages_fetched"] == 2
    assert result["paging"]["total_elements"] == 150
    assert result["paging"]["rows"] == 150
    assert result["paging"]["complete"] is True
    assert result["paging"]["reason"] is None
    assert len(client.calls) == 2


@pytest.mark.asyncio
async def test_fetch_all_pages_short_last_page_no_total():
    """Short page proves end when totalElements is unknown."""
    page1 = {
        "paging": {"page": 1, "size": 100},
        "datas": [{"id": i} for i in range(35)],
    }
    client = MockClient([page1])

    result = await fetch_all_pages(client, "/endpoint", page_size=100)

    assert len(result["datas"]) == 35
    assert result["paging"]["pages_fetched"] == 1
    assert result["paging"]["total_elements"] is None
    assert result["paging"]["complete"] is True
    assert result["paging"]["reason"] is None


@pytest.mark.asyncio
async def test_fetch_all_pages_short_last_page_under_total():
    """Short page before totalElements reached flags incomplete."""
    page1 = {
        "paging": {"page": 1, "size": 100, "totalElements": 100},
        "datas": [{"id": i} for i in range(40)],
    }
    client = MockClient([page1])

    result = await fetch_all_pages(client, "/endpoint", page_size=100)

    assert len(result["datas"]) == 40
    assert result["paging"]["pages_fetched"] == 1
    assert result["paging"]["complete"] is False
    assert "last page was short but only 40 of 100 rows arrived" in result["paging"]["reason"]


@pytest.mark.asyncio
async def test_fetch_all_pages_empty_first_page():
    """Empty first page terminates cleanly and reports complete."""
    page1 = {
        "paging": {"page": 1, "size": 100, "totalElements": 0},
        "datas": [],
    }
    client = MockClient([page1])

    result = await fetch_all_pages(client, "/endpoint", page_size=100)

    assert len(result["datas"]) == 0
    assert result["paging"]["pages_fetched"] == 1
    assert result["paging"]["total_elements"] == 0
    assert result["paging"]["rows"] == 0
    assert result["paging"]["complete"] is True
    assert result["paging"]["reason"] is None


@pytest.mark.asyncio
async def test_fetch_all_pages_max_pages_hit():
    """Exceeding max_pages stops iteration and marks complete=False."""
    pages = [
        {
            "paging": {"page": i, "size": 10, "totalElements": 100},
            "datas": [{"id": j} for j in range((i - 1) * 10, i * 10)],
        }
        for i in range(1, 4)
    ]
    client = MockClient(pages)

    result = await fetch_all_pages(client, "/endpoint", page_size=10, max_pages=2)

    assert result["paging"]["pages_fetched"] == 2
    assert result["paging"]["rows"] == 20
    assert result["paging"]["complete"] is False
    assert result["paging"]["reason"] == "stopped at max_pages=2"


@pytest.mark.asyncio
async def test_fetch_all_pages_missing_datas():
    """Response lacking datas key is incomplete."""
    page1 = {"error": "bad response"}
    client = MockClient([page1])

    result = await fetch_all_pages(client, "/endpoint", page_size=100)

    assert len(result["datas"]) == 0
    assert result["paging"]["pages_fetched"] == 1
    assert result["paging"]["complete"] is False
    assert result["paging"]["reason"] == "response has no datas list"


@pytest.mark.asyncio
async def test_fetch_all_pages_params_clamped_and_forwarded():
    """page_size is clamped to 100 and base params are forwarded."""
    page1 = {
        "paging": {"page": 1, "size": 100, "totalElements": 5},
        "datas": [{"id": 1}],
    }
    client = MockClient([page1])

    await fetch_all_pages(
        client,
        "/reports",
        params={"since": "2026-05-01", "until": "2026-05-07"},
        page_size=250,
    )

    path, params = client.calls[0]
    assert path == "/reports"
    assert params["size"] == 100
    assert params["page"] == 1
    assert params["since"] == "2026-05-01"
    assert params["until"] == "2026-05-07"
