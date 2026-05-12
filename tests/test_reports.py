from line_ads_mcp.tools.reports import _summarize_rows


def test_summarize_rows():
    summary = _summarize_rows(
        [
            {"impressions": 1000, "clicks": 50, "spend": 100.5},
            {"impressions": 500, "clicks": 10, "spend": 20},
        ]
    )

    assert summary == {
        "total_spend": 120.5,
        "total_clicks": 60,
        "total_impressions": 1500,
        "avg_ctr": 4.0,
    }

