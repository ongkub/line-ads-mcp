"""Registry contracts: advertise only callable arguments and safe write defaults."""

import inspect
import json
from types import UnionType
from typing import get_args, get_origin, get_type_hints

import pytest
from jsonschema import Draft202012Validator

from line_ads_mcp import server
from line_ads_mcp.tools import ads, adsets, audiences, campaigns, customer_lists, entities, reach, reports


EXPECTED_NAMES = {
    "list_campaigns", "create_campaign", "update_campaign", "pause_campaign", "resume_campaign",
    "list_adsets", "create_adset", "update_adset", "pause_adset", "resume_adset",
    "upload_media", "create_ad", "get_ad_status", "list_ads", "pause_ad", "resume_ad",
    "get_report", "get_daily_report", "get_weekly_report", "list_audiences",
    "list_advanced_targeting_codes", "create_audience", "get_entity", "estimate_adset_reach",
    "check_spend_cap", "sync_ad_daily_csv",
    "upload_customer_list", "get_customer_list_upload_status",
}
APPROVAL = "ต้องให้ผู้ใช้พิมพ์ ยืนยัน หลังเห็น dry run ก่อนส่ง dry_run=false"


def _variants(prop):
    return prop.get("anyOf", [prop])


def _assert_type_contract(prop, annotation):
    """Compare types independently of how nullable schemas are represented."""
    variants = _variants(prop)
    actual = set()
    for variant in variants:
        value = variant["type"]
        actual.update(value if isinstance(value, list) else [value])
    annotations = get_args(annotation) if get_origin(annotation) is UnionType else (annotation,)
    type_names = {str: "string", int: "integer", float: "number", bool: "boolean", type(None): "null"}
    expected = set()
    for item in annotations:
        origin = get_origin(item)
        if origin is list:
            expected.add("array")
            array = next(variant for variant in variants if variant.get("type") == "array")
            _assert_type_contract(array["items"], get_args(item)[0])
        elif origin is dict:
            expected.add("object")
        else:
            expected.add(type_names[item])
    assert actual == expected


@pytest.mark.parametrize("name", sorted(server.TOOLS))
def test_registry_matches_function_signature(name):
    description, schema, function = server.TOOLS[name]
    parameters = inspect.signature(function).parameters
    assert function.__name__ == name
    assert description
    assert set(schema["properties"]) == set(parameters)
    assert schema["required"] == [
        name for name, parameter in parameters.items()
        if parameter.default is inspect.Parameter.empty
    ]
    assert schema["additionalProperties"] is False
    Draft202012Validator.check_schema(schema)
    hints = get_type_hints(function)
    for parameter_name, parameter in parameters.items():
        prop = schema["properties"][parameter_name]
        _assert_type_contract(prop, hints[parameter_name])
        if parameter.default is inspect.Parameter.empty:
            assert "default" not in prop
        else:
            assert "default" in prop
            assert prop["default"] == parameter.default
            Draft202012Validator(prop).validate(prop["default"])


@pytest.mark.parametrize("name", sorted(server.TOOLS))
def test_write_defaults_and_confirmation_description(name):
    description, schema, function = server.TOOLS[name]
    parameters = inspect.signature(function).parameters
    if "dry_run" in parameters:
        assert parameters["dry_run"].default is True
        assert schema["properties"]["dry_run"]["default"] is True
        assert "เขียน" in description
        assert "dry_run=True" in description
        assert APPROVAL in description
    else:
        assert "อ่านอย่างเดียว" in description
    # create_audience has no status parameter: do not invent one for it.
    if name.startswith("create_") and "status" in parameters:
        assert parameters["status"].default == "PAUSED"
        assert schema["properties"]["status"]["default"] == "PAUSED"
        assert set(schema["properties"]["status"]["enum"]) == {"PAUSED", "ACTIVE"}


# Use the function module's validation constants, not copies of registry enum values.
ENUM_CONSTANTS = {
    "list_campaigns": {"status": campaigns.CAMPAIGN_STATUS_FILTER},
    "list_adsets": {"status": adsets.ADSET_STATUS_FILTER},
    "list_ads": {"status": ads.AD_STATUS_FILTER},
    "create_campaign": {"objective": campaigns.OBJECTIVES, "status": campaigns.STATUSES},
    "update_campaign": {"status": campaigns.STATUSES},
    "create_adset": {
        "status": adsets.STATUSES, "bid_type": adsets.BID_TYPES,
        "bid_strategy": adsets.BID_STRATEGIES, "auto_bid_type": adsets.AUTO_BID_TYPES,
        "targeting_mode": adsets.TARGETING_MODES,
        "age_min": adsets.VALID_AGE_MIN, "age_max": adsets.VALID_AGE_MAX,
    },
    "update_adset": {
        "status": adsets.STATUSES, "targeting_mode": adsets.TARGETING_MODES,
        "age_min": adsets.VALID_AGE_MIN, "age_max": adsets.VALID_AGE_MAX,
    },
    "create_ad": {"call_to_action": ads.CALL_TO_ACTIONS, "creative_format": ads.CREATIVE_FORMATS},
    "get_report": {"level": reports.REPORT_LEVELS},
    "get_daily_report": {"level": reports.REPORT_LEVELS},
    "get_weekly_report": {"level": reports.REPORT_LEVELS},
    "create_audience": {"function_type": audiences.AUDIENCE_FUNCTION_TYPES},
    "upload_customer_list": {"id_type": customer_lists.ID_TYPES, "action": customer_lists.ACTIONS},
    "get_entity": {"entity_type": entities.VALID_ENTITY_TYPES},
    "estimate_adset_reach": {
        "campaign_objective": reach.OBJECTIVES, "bid_type": reach.ARS_BID_TYPES,
        "bid_strategy": reach.BID_STRATEGIES, "auto_bid_type": reach.AUTO_BID_TYPES,
        "age_min": adsets.VALID_AGE_MIN, "age_max": adsets.VALID_AGE_MAX,
    },
}


@pytest.mark.parametrize("name", sorted(server.TOOLS))
def test_enums_are_supported_by_module_constants(name):
    properties = server.TOOLS[name][1]["properties"]
    constants = ENUM_CONSTANTS.get(name, {})
    for parameter_name, prop in properties.items():
        for variant in _variants(prop):
            if "enum" in variant:
                allowed = constants.get(parameter_name)
                if allowed is not None:
                    assert variant["enum"]
                    assert set(variant["enum"]) <= allowed
                else:
                    # Ad create validates status against an inline literal set.
                    assert (name, parameter_name) == ("create_ad", "status")
                    assert set(variant["enum"]) <= {"ACTIVE", "PAUSED"}
    for parameter_name in constants:
        assert any("enum" in variant for variant in _variants(properties[parameter_name]))


def test_report_page_size_and_simulation_contracts():
    prop = server.TOOLS["get_report"][1]["properties"]["page_size"]
    assert prop["maximum"] == 100
    assert prop["default"] == 100
    description, schema, _ = server.TOOLS["estimate_adset_reach"]
    assert "ค่าประมาณ ไม่สร้างอะไร" in description
    assert "dry_run" not in schema["properties"]
    assert "workspace_dir" not in schema["properties"]


async def test_list_tools_returns_every_registered_contract():
    tools = await server.list_tools()
    assert set(server.TOOLS) == EXPECTED_NAMES
    assert "get_adset_audience_size" not in server.TOOLS
    assert len(tools) == len(EXPECTED_NAMES)
    assert {tool.name for tool in tools} == EXPECTED_NAMES
    for tool in tools:
        description, schema, _ = server.TOOLS[tool.name]
        assert tool.description == description
        assert tool.inputSchema == schema


@pytest.mark.parametrize("arguments", [None, {}])
async def test_call_tool_unknown_returns_ok_false(arguments):
    response = await server.call_tool("unknown_tool", arguments)
    assert len(response) == 1
    assert response[0].type == "text"
    assert json.loads(response[0].text)["ok"] is False


async def test_call_tool_dispatches_arguments_without_network(monkeypatch):
    calls = []

    async def fake_tool(**arguments):
        calls.append(arguments)
        return {"ok": True, "data": {"name": "ตัวอย่าง"}}

    description, schema, _ = server.TOOLS["get_entity"]
    monkeypatch.setitem(server.TOOLS, "get_entity", (description, schema, fake_tool))
    arguments = {"entity_type": "ad", "entity_id": "123"}
    response = await server.call_tool("get_entity", arguments)
    assert calls == [arguments]
    assert json.loads(response[0].text) == {"ok": True, "data": {"name": "ตัวอย่าง"}}
