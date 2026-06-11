# KiasuMiles OpenAI Case Study

## One-Line Summary

KiasuMiles turns a high-friction real-world decision - which Singapore miles card to use at checkout - into a local, offline MCP workflow that any agent can call.

## Problem

Singapore miles optimizers often know the rules in theory but fail at the point of purchase. The same merchant can post under different MCCs, wallet-specific card ownership matters, monthly caps matter, and the user usually needs the answer quickly.

Generic model knowledge is not enough because card rules drift, merchant MCCs are specific, and the user's wallet is personal context.

## Product Bet

The agent should not be the source of truth for card rules. The agent should orchestrate a small local tool that knows:

- the user's wallet,
- merchant MCC data,
- card earn rules,
- caps and caveats,
- and how to present a short checkout-ready answer.

## Architecture

KiasuMiles is a Python MCP server with a local stdio transport. Query-time recommendations use bundled CSV data and a local wallet file, so no hosting or API key is needed for the core workflow.

The current architecture separates:

- `kiasumiles.engine`: merchant matching, wallet storage, card ranking,
- `kiasumiles.tools`: transport-neutral tool handlers,
- `kiasumiles.server`: thin FastMCP adapter,
- `kiasumiles.agent_contract`: tool descriptions and display rules for agents,
- `plugins/kiasumiles`: Codex plugin packaging and skill guidance.

## Why This Is Codex-Friendly

Codex can inspect the repo, run the tests, understand the domain vocabulary in `CONTEXT.md`, and install the repo-scoped plugin through `.agents/plugins/marketplace.json`.

The plugin bundles both MCP config and a skill. That matters because MCP exposes capability, while the skill teaches agent behavior: when to call the tool, how to configure the wallet, and what not to show the user.

## Why This Is ChatGPT-App-Ready

The business logic no longer lives inside the FastMCP decorator layer. A hosted ChatGPT Apps SDK adapter can import `kiasumiles.tools`, register the same tool descriptions from `kiasumiles.agent_contract`, and decide separately how ChatGPT user wallet state should be stored.

That keeps the local MCP product and future hosted ChatGPT app aligned without duplicating card-routing logic.

## What Changed In This Iteration

- Added an agent contract module with reusable tool descriptions and display rules.
- Split reusable tool handlers from the MCP server adapter.
- Added `kiasumiles_agent_guide` for agent self-orientation.
- Added a repo-scoped Codex plugin scaffold with MCP config and a KiasuMiles skill.
- Added `CONTEXT.md` and `AGENTS.md` so future agents share the same vocabulary and commands.
- Fixed `CardRule` defaults so tests and fixtures do not need to know every CSV column.

## Good Interview Thread

The interesting part is not just "I built an MCP server." It is that MCP gives the model a reliable local capability, while Codex plugin packaging gives the model durable operating instructions. The combination turns a fragile prompt into a repeatable product surface.

## Next Decisions

- Decide how a hosted ChatGPT app should store wallet state.
- Decide whether the ChatGPT app needs UI, or whether tool-only is enough.
- Add CI and publish plugin installation instructions after the repo hygiene pass.
