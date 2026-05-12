"""LINE Ads code lookup tools."""

from __future__ import annotations

from typing import Any

from line_ads_mcp.client import LineAdsClient, LineAdsConfig

from .common import handle_tool_error, ok


async def list_advanced_targeting_codes(
    campaign_objective: str = "GAIN_FRIENDS",
    country: str = "TH",
    locale: str = "th",
) -> dict[str, Any]:
    """List official advanced targeting codes.

    Use this before setting interest targeting. The adgroup payload must use
    selectable code values, not human labels such as "Marketing" or "Business".
    """
    try:
        config = LineAdsConfig.from_env()
        async with LineAdsClient(config) as client:
            data = await client.get(
                "/codes/advanced-targeting",
                params={
                    "campaignObjective": campaign_objective,
                    "country": country,
                    "locale": locale,
                },
            )
        return ok(data)
    except Exception as error:
        return handle_tool_error(error)
