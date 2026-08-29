import asyncio
import json

from kiasumiles import hosted


def test_new_tools_are_callable_through_mcp_with_generated_schemas():
    async def exercise():
        tools = {tool.name: tool for tool in await hosted.mcp.list_tools()}
        compare = tools["kiasumiles_compare_payment_methods"]
        changes = tools["kiasumiles_changes_since"]

        assert "amount_sgd" in compare.inputSchema["properties"]
        assert changes.inputSchema["required"] == ["since"]

        result = await hosted.mcp.call_tool(
            "kiasumiles_compare_payment_methods",
            {
                "merchant": "NTUC FairPrice",
                "cards": ["citi_rewards_mc", "amaze"],
                "amount_sgd": 20,
            },
        )
        payload = json.loads(result[0].text)
        assert payload["wallet_stored"] is False
        assert payload["methods"][-1]["payment_method"] == "amaze"

        result = await hosted.mcp.call_tool(
            "kiasumiles_changes_since", {"since": "2026-08-01"}
        )
        payload = json.loads(result[0].text)
        assert payload["changes"]
        assert all("source" not in key for row in payload["changes"] for key in row)

    asyncio.run(exercise())
