from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .agent_contract import TOOL_DESCRIPTIONS
from . import tools

mcp = FastMCP("KiasuMiles")


def kiasumiles_list_cards(bank: str | None = None) -> dict:
    return tools.list_cards(bank)


def kiasumiles_configure(cards: list[str]) -> dict:
    return tools.configure(cards)


def kiasumiles_get_wallet() -> dict:
    return tools.get_wallet()


def kiasumiles_lookup(
    merchant: str,
    outlet: str | None = None,
    channel: str | None = None,
    category: str | None = None,
) -> dict:
    return tools.lookup(merchant, outlet, channel, category)


def kiasumiles_recommend_stack(cards: list[str] | None = None, top_n: int = 3) -> dict:
    return tools.recommend_stack(cards, top_n)


def kiasumiles_agent_guide() -> dict:
    return tools.guide()


for _name, _description in TOOL_DESCRIPTIONS.items():
    _tool = globals()[_name]
    _tool.__doc__ = _description
    globals()[_name] = mcp.tool()(_tool)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
