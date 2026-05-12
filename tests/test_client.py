import json

import httpx
import pytest

from line_ads_mcp.client import LineAdsAPIError, LineAdsClient, LineAdsConfig


@pytest.mark.asyncio
async def test_client_signs_and_normalizes_path():
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"ok": True})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = LineAdsClient(
            LineAdsConfig("access", "secret", "https://ads.line.me/api/v3", "A123"),
            http_client,
        )
        data = await client.get("/v3/adaccounts/A123/campaigns")

    assert data == {"ok": True}
    assert str(requests[0].url) == "https://ads.line.me/api/v3/adaccounts/A123/campaigns"
    assert requests[0].headers["Authorization"].startswith("Bearer ey")
    assert requests[0].headers["Date"]


@pytest.mark.asyncio
async def test_client_raises_thai_error_for_401():
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "bad signature"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = LineAdsClient(LineAdsConfig("access", "secret"), http_client)
        with pytest.raises(LineAdsAPIError) as exc_info:
            await client.get("/adaccounts/A123/campaigns")

    assert "credentials" in exc_info.value.message or "signature" in exc_info.value.message
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_client_sends_compact_json_body():
    bodies = []

    async def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(request.content.decode())
        return httpx.Response(200, json={"created": True})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = LineAdsClient(LineAdsConfig("access", "secret"), http_client)
        await client.post("/adaccounts/A123/campaigns", {"name": "ทดสอบ", "dailyBudget": 300})

    assert bodies == [json.dumps({"name": "ทดสอบ", "dailyBudget": 300}, ensure_ascii=False, separators=(",", ":"))]



@pytest.mark.asyncio
async def test_get_request_does_not_send_content_type_header():
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"ok": True})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = LineAdsClient(LineAdsConfig("access", "secret"), http_client)
        await client.get("/adaccounts/A123/campaigns")

    assert "Content-Type" not in requests[0].headers
