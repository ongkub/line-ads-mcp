"""Page-through helper for LINE Ads list/report endpoints.

LINE Ads API v3 list and online-report endpoints accept ``page`` (1-based) and
``size`` and return ``{"paging": {"page", "size", "totalElements"}, "datas": [...]}``.
Online reports cap ``size`` at 100.
"""

from __future__ import annotations

from typing import Any

from line_ads_mcp.client import LineAdsClient

MAX_PAGE_SIZE = 100


async def fetch_all_pages(
    client: LineAdsClient,
    path: str,
    params: dict[str, Any] | None = None,
    page_size: int = MAX_PAGE_SIZE,
    max_pages: int = 50,
) -> dict[str, Any]:
    """Fetch every page of ``path`` and report whether the result is complete.

    Returns ``{"datas": [...], "paging": {"pages_fetched", "total_elements", "complete", "reason"}}``.
    ``complete`` is True only when the API reported ``totalElements`` and we collected that many rows,
    or when a short/empty page proves we reached the end.
    """
    size = max(1, min(int(page_size), MAX_PAGE_SIZE))
    base = dict(params or {})
    rows: list[Any] = []
    total: int | None = None
    pages = 0
    reason = None
    complete = False

    for page in range(1, max(1, int(max_pages)) + 1):
        data = await client.get(path, params={**base, "page": page, "size": size})
        pages += 1
        batch = data.get("datas") if isinstance(data, dict) else None
        if not isinstance(batch, list):
            reason = "response has no datas list"
            break
        rows.extend(batch)
        paging = data.get("paging") if isinstance(data, dict) else None
        if isinstance(paging, dict) and isinstance(paging.get("totalElements"), int):
            total = paging["totalElements"]
        if total is not None and len(rows) >= total:
            complete = True
            break
        if len(batch) < size:
            complete = total is None or len(rows) >= total
            if not complete:
                reason = f"last page was short but only {len(rows)} of {total} rows arrived"
            break
    else:
        reason = f"stopped at max_pages={max_pages}"

    return {
        "datas": rows,
        "paging": {
            "pages_fetched": pages,
            "total_elements": total,
            "rows": len(rows),
            "complete": complete,
            "reason": reason,
        },
    }
