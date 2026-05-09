from __future__ import annotations
import json
import shutil
import subprocess
import sys
from pathlib import Path


_CLAUDE_DESKTOP = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
_OPENCLAW = Path.home() / ".openclaw" / "config.json"
_HERMES = Path.home() / ".hermes" / "mcp.json"


def find_binary() -> Path | None:
    found = shutil.which("kiasumiles-mcp")
    if found:
        return Path(found)
    fallback = Path(sys.executable).parent / "kiasumiles-mcp"
    if fallback.exists():
        return fallback
    return None


def setup_json_config(config_path: Path, agent_name: str, binary: str) -> bool:
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            config = {}
    else:
        config = {}
    if not isinstance(config, dict):
        config = {}
    config.setdefault("mcpServers", {})
    config["mcpServers"]["kiasumiles"] = {"command": binary}
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return True


def _setup_claude_code(binary: str) -> bool:
    if not shutil.which("claude"):
        return False
    subprocess.run(["claude", "mcp", "remove", "kiasumiles"],
                   capture_output=True)
    result = subprocess.run(
        ["claude", "mcp", "add", "kiasumiles", binary],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def main() -> None:
    print("\nKiasuMiles Setup\n")

    binary = find_binary()
    if binary is None:
        print("Error: kiasumiles-mcp not found.")
        print("Run: pip install kiasumiles-mcp")
        sys.exit(1)

    print(f"Found: {binary}\n")

    configured: list[str] = []
    skipped: list[str] = []

    # Claude Desktop
    if _CLAUDE_DESKTOP.exists() or (_CLAUDE_DESKTOP.parent.exists()):
        setup_json_config(_CLAUDE_DESKTOP, "Claude Desktop", str(binary))
        configured.append("Claude Desktop")
        print("  ✓ Claude Desktop  →  restart Claude Desktop to apply")
    else:
        skipped.append("Claude Desktop")

    # Claude Code
    if shutil.which("claude"):
        if _setup_claude_code(str(binary)):
            configured.append("Claude Code")
            print("  ✓ Claude Code     →  restart Claude Code to apply")
        else:
            print("  ✗ Claude Code     →  failed to register (run: claude mcp add kiasumiles " + str(binary) + ")")
    else:
        skipped.append("Claude Code")

    # OpenClaw
    if _OPENCLAW.exists():
        setup_json_config(_OPENCLAW, "OpenClaw", str(binary))
        configured.append("OpenClaw")
        print("  ✓ OpenClaw        →  restart OpenClaw to apply")
    else:
        skipped.append("OpenClaw")

    # Hermes
    if _HERMES.exists():
        setup_json_config(_HERMES, "Hermes", str(binary))
        configured.append("Hermes")
        print("  ✓ Hermes          →  restart Hermes to apply")
    else:
        skipped.append("Hermes")

    print()
    if configured:
        print("Connected: " + " · ".join(f"{a} ✓" for a in configured))
    if skipped:
        print("Not found: " + ", ".join(skipped))
    if not configured:
        print("No agents detected. Install Claude Desktop, Claude Code, OpenClaw, or Hermes first, then run kiasumiles-setup again.")
        sys.exit(1)

    print("\nDone. Restart your agent, then ask:")
    print('  "Set up my KiasuMiles wallet"')


if __name__ == "__main__":
    main()
