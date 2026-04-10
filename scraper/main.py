#!/usr/bin/env python3
"""
Cyber Intel Scraper — main entry point
Fetches RSS feeds, scores articles, persists to data.json
"""
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

from sources import SOURCES
from scoring import bm25_score, detect_categories, has_critical_theme, normalize_scores
from storage import merge_and_save
from alerts import alert_critical, alert_summary

FETCH_TIMEOUT = 15
USER_AGENT = "CyberIntelBot/1.0 (+https://github.com/your-username/cyber-intel)"


def fetch_feed(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ✗ fetch error: {e}")
        return None


def parse_feed(xml: str, source_name: str) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        print(f"  ✗ parse error: {e}")
        return items

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "dc":   "http://purl.org/dc/elements/1.1/",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }

    # Detect feed type
    is_atom = root.tag.endswith("feed")

    if is_atom:
        entries = root.findall("atom:entry", ns) or root.findall("{http://www.w3.org/2005/Atom}entry")
        for entry in entries:
            def get(tag):
                el = entry.find(f"atom:{tag}", ns) or entry.find(f"{{http://www.w3.org/2005/Atom}}{tag}")
                return el.text.strip() if el is not None and el.text else ""

            title = get("title")
            url = ""
            link_el = entry.find("atom:link", ns) or entry.find("{http://www.w3.org/2005/Atom}link")
            if link_el is not None:
                url = link_el.get("href", "")
            summary = get("summary") or get("content")
            published = get("published") or get("updated") or datetime.now(timezone.utc).isoformat()

            if title and url:
                items.append({"title": title, "url": url,
                               "summary": summary[:500], "published_raw": published})
    else:
        # RSS
        for item in root.iter("item"):
            def get(tag):
                el = item.find(tag) or item.find(f"dc:{tag}", ns)
                return el.text.strip() if el is not None and el.text else ""

            title   = get("title")
            url     = get("link")
            summary = get("description") or get("summary")
            pub     = get("pubDate") or get("date") or datetime.now(timezone.utc).isoformat()

            if title and url:
                items.append({"title": title, "url": url,
                               "summary": summary[:500], "published_raw": pub})

    return items


def parse_date(raw: str) -> str:
    """Normalise various date formats to ISO 8601 UTC."""
    from email.utils import parsedate_to_datetime
    try:
        dt = parsedate_to_datetime(raw)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw[:19], fmt[:len(raw[:19])])
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except Exception:
            pass
    return datetime.now(timezone.utc).isoformat()


def score_item(item: dict, source_name: str) -> dict:
    text = f"{item['title']} {item['title']} {item['title']} {item['summary']}"
    raw = bm25_score(text)
    critical = has_critical_theme(text)
    categories = detect_categories(text)
    published = parse_date(item["published_raw"])

    return {
        "title":      item["title"],
        "url":        item["url"],
        "summary":    item["summary"],
        "source":     source_name,
        "published":  published,
        "raw_score":  raw,
        "score":      0,          # filled by normalize_scores
        "is_relevant": False,     # filled by normalize_scores
        "critical":   critical,
        "categories": categories,
    }


def main():
    print(f"🛡  Cyber Intel Scraper — {datetime.now(timezone.utc).isoformat()}")
    all_items = []

    for source in SOURCES:
        print(f"  Fetching: {source['name']} ...")
        xml = fetch_feed(source["url"])
        if not xml:
            continue
        parsed = parse_feed(xml, source["name"])
        scored = [score_item(i, source["name"]) for i in parsed]
        all_items.extend(scored)
        time.sleep(0.3)  # polite crawl delay

    print(f"\n  Scraped {len(all_items)} articles from {len(SOURCES)} sources")

    all_items = normalize_scores(all_items)
    data = merge_and_save(all_items)

    stats = data["stats"]
    print(f"  Relevant: {stats['relevant']} | Critical: {stats['critical']} | New: {stats['new_this_run']}")

    critical_new = [i for i in all_items if i.get("critical") and i.get("is_relevant")]
    if critical_new:
        print(f"\n  🚨 {len(critical_new)} critical items — sending Telegram alert")
        alert_critical(critical_new)
    else:
        alert_summary(stats)

    print("\n  ✅ Done — data.json updated")


if __name__ == "__main__":
    main()
