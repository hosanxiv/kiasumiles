from __future__ import annotations
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def _get_claude_desktop_config_path() -> Path:
    """Get Claude Desktop config path for current platform."""
    system = platform.system()
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    else:
        # Fallback to Linux convention
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


_CLAUDE_DESKTOP = _get_claude_desktop_config_path()


def find_binary() -> Path | None:
    found = shutil.which("kiasumiles-mcp")
    if found:
        return Path(found)
    fallback = Path(sys.executable).parent / "kiasumiles-mcp"
    if fallback.exists():
        return fallback
    return None


def _setup_claude_desktop(binary: str) -> bool:
    if not (_CLAUDE_DESKTOP.exists() or _CLAUDE_DESKTOP.parent.exists()):
        return False
    config = {}
    if _CLAUDE_DESKTOP.exists():
        try:
            config = json.loads(_CLAUDE_DESKTOP.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            config = {}
    if not isinstance(config, dict):
        config = {}
    config.setdefault("mcpServers", {})
    config["mcpServers"]["kiasumiles"] = {
        "command": "uvx",
        "args": ["kiasumiles-mcp"]
    }
    _CLAUDE_DESKTOP.parent.mkdir(parents=True, exist_ok=True)
    _CLAUDE_DESKTOP.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return True


def _setup_claude_code(binary: str) -> bool:
    if not shutil.which("claude"):
        return False
    subprocess.run(["claude", "mcp", "remove", "kiasumiles"], capture_output=True)
    result = subprocess.run(
        ["claude", "mcp", "add", "kiasumiles", binary],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def main() -> None:
    print("\n" + "=" * 60)
    print("KiasuMiles Setup — Configure your AI agent")
    print("=" * 60 + "\n")

    binary = find_binary()
    if binary is None:
        print("❌ kiasumiles-mcp not found in PATH.")
        print("\nMake sure you've installed it:")
        print("   pip3 install kiasumiles-mcp\n")
        print("Then run this setup again.")
        sys.exit(1)

    print(f"✓ Found kiasumiles-mcp at: {binary}\n")
    print("Configuring your agents...\n")

    configured: list[str] = []
    skipped: list[str] = []

    # Claude Desktop
    if _setup_claude_desktop(str(binary)):
        configured.append("Claude Desktop")
        print("  ✓ Claude Desktop")
    else:
        skipped.append("Claude Desktop")

    # Claude Code
    if shutil.which("claude"):
        if _setup_claude_code(str(binary)):
            configured.append("Claude Code")
            print("  ✓ Claude Code")
        else:
            print("  ⚠ Claude Code (setup failed — try: claude mcp add kiasumiles " + str(binary) + ")")
    else:
        skipped.append("Claude Code")

    print()
    if not configured:
        print("❌ No agents detected.")
        print("\nYou need to install one of these first:")
        print("  • Claude Desktop (https://claude.ai/download)")
        print("  • Claude Code CLI (pip install -U claude-code)")
        print("\nThen run this setup again.\n")
        sys.exit(1)

    print("-" * 60)
    print("\n✅ Setup complete!\n")
    print("Next steps:")
    for agent in configured:
        print(f"\n1. Restart {agent}")
    print("\n2. Then ask any of these:")
    print('   • "Set up my KiasuMiles wallet"')
    print('   • "What card at NTUC FairPrice?"')
    print('   • "Best card for Grab?"')
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
