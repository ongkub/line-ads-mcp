import pytest

from line_ads_mcp.tools.campaigns import create_campaign, pause_campaign, resume_campaign, update_campaign


@pytest.mark.asyncio
async def test_create_campaign_defaults_to_dry_run(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A123")

    result = await create_campaign(
        name="เพิ่มเพื่อน Test",
        objective="GAIN_FRIENDS",
        daily_budget=300,
    )

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["endpoint"] == "/adaccounts/A123/campaigns"


@pytest.mark.asyncio
async def test_create_campaign_payload_uses_micro_units(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A123")

    result = await create_campaign(
        name="เพิ่มเพื่อน Test",
        objective="GAIN_FRIENDS",
        daily_budget=300,
        total_budget=9000,
    )

    payload = result["payload"]
    # 300 THB × 1,000,000 = 300,000,000 micro
    assert payload["dailyBudgetMicro"] == 300_000_000
    # 9000 THB × 1,000,000 = 9,000,000,000 micro
    assert payload["totalBudgetMicro"] == 9_000_000_000
    assert "dailyBudget" not in payload
    assert "totalBudget" not in payload


@pytest.mark.asyncio
async def test_create_campaign_payload_uses_campaignObjective(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A123")

    result = await create_campaign(name="Test", objective="GAIN_FRIENDS")

    payload = result["payload"]
    assert payload["campaignObjective"] == "GAIN_FRIENDS"
    assert "objective" not in payload


@pytest.mark.asyncio
async def test_create_campaign_rejects_old_objective_values(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")

    for bad_objective in ("FRIEND_ADDED", "VISIT_MY_WEBSITE", "APP_INSTALLS", "VIDEO_VIEWS"):
        result = await create_campaign(name="Bad", objective=bad_objective)
        assert result["ok"] is False, f"Should reject {bad_objective}"
        assert "objective" in result["message"]


@pytest.mark.asyncio
async def test_create_campaign_accepts_all_valid_objectives(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A123")

    for obj in ("GAIN_FRIENDS", "WEBSITE_TRAFFIC", "CONVERSIONS", "REACH", "APP_INSTALL", "VIDEO_VIEW"):
        result = await create_campaign(name="Test", objective=obj)
        assert result["ok"] is True, f"Should accept {obj}"
        assert result["payload"]["campaignObjective"] == obj


@pytest.mark.asyncio
async def test_update_campaign_uses_configuredStatus(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A123")

    result = await update_campaign(campaign_id="9652193645389", status="PAUSED")

    payload = result["payload"]
    assert payload["configuredStatus"] == "PAUSED"
    assert "status" not in payload


@pytest.mark.asyncio
async def test_update_campaign_budget_in_micro(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A123")

    result = await update_campaign(campaign_id="9652193645389", daily_budget=500)

    payload = result["payload"]
    assert payload["dailyBudgetMicro"] == 500_000_000
    assert "dailyBudget" not in payload


@pytest.mark.asyncio
async def test_pause_campaign_dry_run_by_default(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A123")

    result = await pause_campaign("9652193645389")

    assert result["dry_run"] is True
    assert result["payload"]["configuredStatus"] == "PAUSED"


@pytest.mark.asyncio
async def test_resume_campaign_dry_run_by_default(monkeypatch):
    monkeypatch.setenv("LINE_ADS_ACCESS_KEY", "access")
    monkeypatch.setenv("LINE_ADS_SECRET_KEY", "secret")
    monkeypatch.setenv("LINE_ADS_AD_ACCOUNT_ID", "A123")

    result = await resume_campaign("9652193645389")

    assert result["dry_run"] is True
    assert result["payload"]["configuredStatus"] == "ACTIVE"
