from kiasumiles.agent_contract import CATEGORY_MCC, HOSTED_TOOL_DESCRIPTIONS, hosted_agent_guide
from kiasumiles import tools


def test_agent_guide_lists_tools_and_display_rules():
    guide = hosted_agent_guide()
    tool_names = {tool["name"] for tool in guide["tools"]}

    assert guide["name"] == "KiasuMiles Hosted"
    assert "kiasumiles_lookup" in tool_names
    assert "kiasumiles_agent_guide" in tool_names
    assert guide["display_rules"]
    assert guide["accepted_categories"]["dining"] == "5812"


def test_tool_descriptions_cover_category_values():
    lookup_description = HOSTED_TOOL_DESCRIPTIONS["kiasumiles_lookup"]

    for category in CATEGORY_MCC:
        assert category in lookup_description


def test_tool_handlers_are_callable_without_fastmcp():
    result = tools.lookup_hosted("NTUC FairPrice", cards=["uob_ppv"])

    assert result["merchant"] == "NTUC FairPrice"
    assert result["recommendations"]
