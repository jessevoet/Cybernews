import json
import os
from datetime import datetime, timedelta, timezone

DATA_FILE = "../data.json"
WINDOW_DAYS = 7


def load() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"items": [], "updated": None, "stats": {}}


def save(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def prune(items: list[dict]) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
    return [
        i for i in items
        if datetime.fromisoformat(i["published"]) > cutoff
    ]


def deduplicate(existing: list[dict], new_items: list[dict]) -> list[dict]:
    seen_urls = {i["url"] for i in existing}
    seen_titles = {i["title"].lower()[:60] for i in existing}
    fresh = []
    for item in new_items:
        if item["url"] not in seen_urls and item["title"].lower()[:60] not in seen_titles:
            fresh.append(item)
            seen_urls.add(item["url"])
            seen_titles.add(item["title"].lower()[:60])
    return fresh


def merge_and_save(new_items: list[dict]) -> dict:
    data = load()
    existing = data.get("items", [])
    existing = prune(existing)
    fresh = deduplicate(existing, new_items)
    all_items = existing + fresh
    all_items.sort(key=lambda x: x["published"], reverse=True)

    now = datetime.now(timezone.utc).isoformat()
    relevant = [i for i in all_items if i.get("is_relevant")]
    critical = [i for i in all_items if i.get("critical")]

    data = {
        "items": all_items,
        "updated": now,
        "stats": {
            "total": len(all_items),
            "relevant": len(relevant),
            "critical": len(critical),
            "new_this_run": len(fresh),
            "sources": len({i["source"] for i in all_items}),
        }
    }
    save(data)
    return data
