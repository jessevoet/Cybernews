import os
import urllib.request
import urllib.parse
import json

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(url, data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")


def alert_critical(items: list[dict]):
    if not items:
        return
    lines = ["🚨 <b>CYBER INTEL — CRITICAL ALERTS</b>\n"]
    for item in items[:5]:  # max 5 per run
        cats = ", ".join(item.get("categories", ["General"]))
        lines.append(
            f"• <b>[{cats}]</b> {item['title']}\n"
            f"  <i>{item['source']}</i> — <a href='{item['url']}'>Read</a>\n"
        )
    send_telegram("\n".join(lines))


def alert_summary(stats: dict):
    if not TELEGRAM_TOKEN:
        return
    msg = (
        f"📡 <b>Cyber Intel Digest</b>\n"
        f"Relevant: {stats.get('relevant', 0)} | "
        f"Critical: {stats.get('critical', 0)} | "
        f"New: {stats.get('new_this_run', 0)}"
    )
    send_telegram(msg)
