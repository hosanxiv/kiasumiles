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
    config["mcpServers"]["kiasumiles"] = {"command": binary}
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
    print("\nKiasuMiles Setup\n")

    binary = find_binary()
    if binary is None:
        print("Error: kiasumiles-mcp not found.")
        print("Run: pip3 install kiasumiles-mcp  (or: uv tool install / pipx install)")
        sys.exit(1)

    print(f"Found: {binary}\n")

    configured: list[str] = []
    skipped: list[str] = []

    if _setup_claude_desktop(str(binary)):
        configured.append("Claude Desktop")
        print("  ✓ Claude Desktop  →  restart Claude Desktop to apply")
    else:
        skipped.append("Claude Desktop")

    if shutil.which("claude"):
        if _setup_claude_code(str(binary)):
            configured.append("Claude Code")
            print("  ✓ Claude Code     →  restart Claude Code to apply")
        else:
            print("  ✗ Claude Code     →  failed (run: claude mcp add kiasumiles " + str(binary) + ")")
    else:
        skipped.append("Claude Code")

    print()
    if configured:
        print("Connected: " + " · ".join(f"{a} ✓" for a in configured))
    if skipped:
        print("Not detected: " + ", ".join(skipped))
    if not configured:
        print("No agents detected. Install Claude Desktop or Claude Code first, then run kiasumiles-setup again.")
        print("\nFor OpenClaw or Hermes, see: https://github.com/hosanxiv/kiasumiles#setup")
        sys.exit(1)

    print("\nDone. Restart your agent, then ask:")
    print('  "Set up my KiasuMiles wallet"')


if __name__ == "__main__":
    main()
