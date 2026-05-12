import pytest

from line_ads_mcp.tools.adsets import create_adset, pause_adset, resume_adset, update_adset


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A123")


@pytest.mark.asyncio
async def test_create_adset_defaults_to_dry_run():
    result = await create_adset(
        campaign_id="9652193645389",
        name="Test Adset",
        bid_type="CPF",
        bid_strategy="COST_CAP",
        daily_budget=300,
        bid_amount=10,
    )

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["endpoint"] == "/adaccounts/A123/adgroups"


@pytest.mark.asyncio
async def test_create_adset_budget_in_micro():
    result = await create_adset(
        campaign_id="9652193645389",
        name="Test Adset",
        bid_type="CPF",
        bid_strategy="COST_CAP",
        daily_budget=300,
        bid_amount=10,
    )

    payload = result["payload"]
    # Confirmed from real adset: dailyBudgetMicro: 300000000, bidAmountMicro: 10000000
    assert payload["dailyBudgetMicro"] == 300_000_000
    assert payload["bidAmountMicro"] == 10_000_000
    assert "dailyBudget" not in payload
    assert "bidAmount" not in payload


@pytest.mark.asyncio
async def test_create_adset_includes_bid_type_and_strategy():
    result = await create_adset(
        campaign_id="9652193645389",
        name="Test Adset",
        bid_type="CPF",
        bid_strategy="COST_CAP",
    )

    payload = result["payload"]
    assert payload["bidType"] == "CPF"
    assert payload["bidStrategy"] == "COST_CAP"


@pytest.mark.asyncio
async def test_create_adset_rejects_invalid_bid_type():
    result = await create_adset(
        campaign_id="9652193645389",
        name="Test",
        bid_type="CPX",
        bid_strategy="COST_CAP",
    )

    assert result["ok"] is False
    assert "bid_type" in result["message"]


@pytest.mark.asyncio
async def test_create_adset_rejects_invalid_bid_strategy():
    result = await create_adset(
        campaign_id="9652193645389",
        name="Test",
        bid_type="CPF",
        bid_strategy="TARGET_ROAS",
    )

    assert result["ok"] is False
    assert "bid_strategy" in result["message"]


@pytest.mark.asyncio
async def test_update_adset_uses_configuredStatus():
    result = await update_adset(adset_id="1752193645380", status="PAUSED")

    payload = result["payload"]
    assert payload["configuredStatus"] == "PAUSED"
    assert "status" not in payload


@pytest.mark.asyncio
async def test_update_adset_budget_in_micro():
    result = await update_adset(adset_id="1752193645380", daily_budget=500, bid_amount=15)

    payload = result["payload"]
    assert payload["dailyBudgetMicro"] == 500_000_000
    assert payload["bidAmountMicro"] == 15_000_000
    assert "dailyBudget" not in payload
    assert "bidAmount" not in payload


@pytest.mark.asyncio
async def test_pause_adset_dry_run_by_default():
    result = await pause_adset("1752193645380")

    assert result["dry_run"] is True
    assert result["payload"]["configuredStatus"] == "PAUSED"


@pytest.mark.asyncio
async def test_resume_adset_dry_run_by_default():
    result = await resume_adset("1752193645380")

    assert result["dry_run"] is True
    assert result["payload"]["configuredStatus"] == "ACTIVE"
