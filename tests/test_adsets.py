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
        auto_bid_type="FRIEND",
        daily_budget=100,
        bid_amount=25,
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
        auto_bid_type="FRIEND",
        daily_budget=100,
        bid_amount=25,
    )

    payload = result["payload"]
    assert payload["dailyBudgetMicro"] == 100_000_000
    assert payload["bidAmountMicro"] == 25_000_000
    assert "dailyBudget" not in payload
    assert "bidAmount" not in payload


@pytest.mark.asyncio
async def test_create_adset_includes_auto_bid_type():
    """Verified: autoBidType is required by LINE Ads API."""
    result = await create_adset(
        campaign_id="9652193645389",
        name="Test Adset",
        bid_type="CPF",
        bid_strategy="COST_CAP",
        auto_bid_type="FRIEND",
        daily_budget=100,
        bid_amount=25,
    )

    assert result["payload"]["autoBidType"] == "FRIEND"


@pytest.mark.asyncio
async def test_create_adset_targeting_is_flat_object():
    """Verified: targeting uses flat ageMin/ageMax/country fields, not nested arrays."""
    result = await create_adset(
        campaign_id="9652193645389",
        name="Test Adset",
        bid_type="CPF",
        bid_strategy="COST_CAP",
        auto_bid_type="FRIEND",
        daily_budget=100,
        bid_amount=25,
        age_min=25,
        age_max=54,
    )

    targeting = result["payload"]["targeting"]
    assert targeting["ageMin"] == 25
    assert targeting["ageMax"] == 54
    assert targeting["targetingMode"] == "AUTO"
    assert targeting["country"] == "TH"


@pytest.mark.asyncio
async def test_create_adset_interest_codes_use_manual_advanced_targeting():
    result = await create_adset(
        campaign_id="9652193645389",
        name="Interest Adset",
        bid_type="CPF",
        bid_strategy="COST_CAP",
        auto_bid_type="FRIEND",
        daily_budget=100,
        bid_amount=25,
        age_min=25,
        age_max=44,
        interest_codes=["4"],
        excluded_audience_ids=["5343822743474"],
    )

    targeting = result["payload"]["targeting"]
    assert targeting["targetingMode"] == "MANUAL"
    assert targeting["includeAdvancedTargetings"] == [{"interests": ["4"]}]
    assert targeting["excludedCustomAudienceIds"] == ["5343822743474"]


@pytest.mark.asyncio
async def test_create_adset_excluded_audience_ids_in_targeting():
    """GAIN_FRIENDS campaigns require excludedCustomAudienceIds."""
    result = await create_adset(
        campaign_id="9652193645389",
        name="Test Adset",
        bid_type="CPF",
        bid_strategy="COST_CAP",
        auto_bid_type="FRIEND",
        daily_budget=100,
        bid_amount=25,
        excluded_audience_ids=["5343822743474"],
    )

    targeting = result["payload"]["targeting"]
    assert targeting["excludedCustomAudienceIds"] == ["5343822743474"]


@pytest.mark.asyncio
async def test_update_adset_can_dry_run_interest_targeting_change():
    result = await update_adset(
        adset_id="5563793668113",
        age_min=25,
        age_max=44,
        interest_codes=["4"],
        excluded_audience_ids=["5343822743474"],
    )

    targeting = result["payload"]["targeting"]
    assert targeting["targetingMode"] == "MANUAL"
    assert targeting["includeAdvancedTargetings"] == [{"interests": ["4"]}]


@pytest.mark.asyncio
async def test_create_adset_requires_bid_amount_for_cost_cap():
    result = await create_adset(
        campaign_id="9652193645389",
        name="Test Adset",
        bid_type="CPF",
        bid_strategy="COST_CAP",
        auto_bid_type="FRIEND",
        daily_budget=100,
        bid_amount=None,
    )

    assert result["ok"] is False
    assert "bid_amount" in result["message"]


@pytest.mark.asyncio
async def test_create_adset_lowest_cost_no_bid_amount():
    result = await create_adset(
        campaign_id="9652193645389",
        name="Test Adset",
        bid_type="CPF",
        bid_strategy="LOWEST_COST",
        auto_bid_type="FRIEND",
        daily_budget=100,
    )

    assert result["ok"] is True
    assert "bidAmountMicro" not in result["payload"]


@pytest.mark.asyncio
async def test_create_adset_rejects_invalid_auto_bid_type():
    result = await create_adset(
        campaign_id="9652193645389",
        name="Test",
        bid_type="CPF",
        bid_strategy="COST_CAP",
        auto_bid_type="LIKE",
        daily_budget=100,
        bid_amount=25,
    )

    assert result["ok"] is False
    assert "auto_bid_type" in result["message"]


@pytest.mark.asyncio
async def test_update_adset_uses_configuredStatus():
    result = await update_adset(adset_id="1752193645380", status="PAUSED")

    assert result["payload"]["configuredStatus"] == "PAUSED"
    assert "status" not in result["payload"]


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
