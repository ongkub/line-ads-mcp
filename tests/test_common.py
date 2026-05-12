import pytest

from line_ads_mcp.tools.common import to_micro


@pytest.mark.parametrize(
    "thb, expected_micro",
    [
        (300, 300_000_000),      # confirmed from real adset dailyBudgetMicro: 300000000
        (10, 10_000_000),        # confirmed from real adset bidAmountMicro: 10000000
        (0.5, 500_000),
        (1, 1_000_000),
        (9000, 9_000_000_000),
    ],
)
def test_to_micro(thb, expected_micro):
    assert to_micro(thb) == expected_micro
