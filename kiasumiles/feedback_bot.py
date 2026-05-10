"""Telegram feedback bot for KiasuMiles.

Listens for messages on @kiasumilesbot. Logs each message with sender,
timestamp, and content to ~/.kiasumiles/feedback.log. Acknowledges the
sender with a thank-you reply.

Run continuously on a server (or locally for testing):

    export KIASUMILES_BOT_TOKEN="<token from @BotFather>"
    python3 -m kiasumiles.feedback_bot

The token is read from the env var. NEVER commit the token to git.

Optional: set KIASUMILES_OWNER_CHAT_ID to forward feedback to a specific
chat (e.g. your own Telegram). The bot prints the owner chat ID on /start.
"""
from __future__ import annotations
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import request as urlrequest, parse as urlparse, error as urlerror


API_BASE = "https://api.telegram.org/bot"
LOG_DIR = Path.home() / ".kiasumiles"
LOG_FILE = LOG_DIR / "feedback.log"

ACK_REPLY = (
    "Thanks for the feedback on KiasuMiles. Logged it — "
    "we look at every report. If your card recommendation was wrong, "
    "include the merchant name and which card was suggested."
)


def _api(token: str, method: str, payload: dict | None = None) -> dict:
    url = f"{API_BASE}{token}/{method}"
    data = urlparse.urlencode(payload or {}).encode() if payload else None
    req = urlrequest.Request(url, data=data, method="POST" if data else "GET")
    try:
        with urlrequest.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urlerror.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.read().decode()[:200]}"}
    except (urlerror.URLError, TimeoutError) as e:
        return {"ok": False, "error": str(e)}


def _log_feedback(msg: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    sender = msg.get("from", {})
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "chat_id": msg.get("chat", {}).get("id"),
        "user_id": sender.get("id"),
        "username": sender.get("username") or "",
        "name": (sender.get("first_name", "") + " " + sender.get("last_name", "")).strip(),
        "text": msg.get("text", ""),
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[{entry['ts']}] {entry['username'] or entry['name']}: {entry['text'][:100]}")


def _handle_message(token: str, msg: dict, owner_chat_id: str | None) -> None:
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "")
    if not chat_id:
        return

    if text.startswith("/start"):
        _api(token, "sendMessage", {
            "chat_id": chat_id,
            "text": (
                "Hi — this is the KiasuMiles feedback bot.\n\n"
                "Send a message describing what was wrong (e.g. card recommendation, "
                "earn rate, merchant MCC). Include the merchant name. "
                "We log everything and review weekly."
            ),
        })
        print(f"[/start] chat_id={chat_id} username=@{msg.get('from', {}).get('username', '')}")
        return

    _log_feedback(msg)
    _api(token, "sendMessage", {"chat_id": chat_id, "text": ACK_REPLY})

    if owner_chat_id and str(chat_id) != str(owner_chat_id):
        sender = msg.get("from", {})
        forward = (
            f"Feedback from @{sender.get('username', '?')} ({sender.get('id', '?')}):\n\n"
            f"{text}"
        )
        _api(token, "sendMessage", {"chat_id": owner_chat_id, "text": forward})


def main() -> None:
    token = os.environ.get("KIASUMILES_BOT_TOKEN", "").strip()
    if not token:
        print("ERROR: set KIASUMILES_BOT_TOKEN env var first.", file=sys.stderr)
        print("Get a token from @BotFather on Telegram.", file=sys.stderr)
        sys.exit(1)

    owner_chat_id = os.environ.get("KIASUMILES_OWNER_CHAT_ID", "").strip() or None

    me = _api(token, "getMe")
    if not me.get("ok"):
        print(f"ERROR: bot token rejected by Telegram: {me.get('error') or me}", file=sys.stderr)
        sys.exit(1)
    bot_username = me["result"].get("username", "?")
    print(f"KiasuMiles feedback bot online: @{bot_username}")
    print(f"Logging to: {LOG_FILE}")
    if owner_chat_id:
        print(f"Forwarding to owner chat: {owner_chat_id}")
    print("Waiting for messages... (Ctrl+C to stop)\n")

    offset = 0
    while True:
        result = _api(token, "getUpdates", {"offset": offset, "timeout": 30})
        if not result.get("ok"):
            print(f"poll error: {result.get('error')}", file=sys.stderr)
            time.sleep(5)
            continue
        for update in result.get("result", []):
            offset = update["update_id"] + 1
            msg = update.get("message")
            if msg:
                try:
                    _handle_message(token, msg, owner_chat_id)
                except Exception as e:
                    print(f"handler error: {e}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nstopped.")
