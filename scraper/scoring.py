import math
import re
from collections import Counter

# ── Weighted keyword taxonomy ──────────────────────────────────────────────────
KEYWORDS = {
    # Critical — active threats
    "ransomware":           10,
    "zero-day":             10,
    "zero day":             10,
    "0day":                 10,
    "critical vulnerability":10,
    "actively exploited":   10,
    "nation state":         10,
    "apt":                   9,
    "supply chain attack":   9,
    "data breach":           9,
    "rce":                   9,
    "remote code execution": 9,
    "backdoor":              8,
    "malware":               8,
    "phishing":              7,
    "credential theft":      8,
    "privilege escalation":  8,
    "lateral movement":      8,
    "c2":                    7,
    "command and control":   7,

    # Vulnerability / CVE
    "cve":                   7,
    "patch tuesday":         7,
    "out of band":           7,
    "proof of concept":      7,
    "poc":                   6,
    "exploit":               8,
    "buffer overflow":       7,
    "sql injection":         6,
    "xss":                   5,
    "ssrf":                  6,
    "deserialization":       7,

    # Infrastructure & sectors
    "critical infrastructure": 9,
    "ics":                   8,
    "scada":                 8,
    "ot security":           8,
    "healthcare":            6,
    "hospital":              6,
    "energy sector":         7,
    "financial sector":      6,
    "government":            6,
    "election":              7,

    # Threat actors & operations
    "lazarus":               9,
    "cozy bear":             9,
    "fancy bear":            9,
    "sandworm":              9,
    "volt typhoon":          9,
    "lockbit":               9,
    "cl0p":                  8,
    "blackcat":              8,
    "alphv":                 8,
    "scattered spider":      8,
    "threat actor":          7,
    "cybercriminal":         6,

    # Defensive / incident
    "incident response":     6,
    "ioc":                   6,
    "indicators of compromise": 7,
    "takedown":              6,
    "law enforcement":       5,
    "indictment":            7,
    "arrest":                6,
    "fbi":                   5,
    "cisa":                  6,
    "nsa":                   5,

    # General cyber
    "vulnerability":         5,
    "patch":                 4,
    "cybersecurity":         3,
    "security":              2,
    "hacker":                4,
    "breach":                7,
    "leak":                  5,
    "dark web":              5,
    "botnet":                7,
    "ddos":                  6,
    "wiper":                 9,
    "spyware":               8,
    "stalkerware":           7,
}

# Critical themes that always get surfaced regardless of score
CRITICAL_THEMES = [
    "zero-day", "zero day", "0day", "actively exploited",
    "ransomware", "nation state", "supply chain attack",
    "critical infrastructure", "wiper", "data breach",
    "rce", "remote code execution", "backdoor",
]

CATEGORY_TAGS = {
    "Ransomware":       ["ransomware", "lockbit", "cl0p", "blackcat", "alphv"],
    "APT / Nation State": ["apt", "nation state", "lazarus", "cozy bear", "fancy bear",
                           "sandworm", "volt typhoon", "scattered spider"],
    "Vulnerability":    ["cve", "zero-day", "zero day", "exploit", "patch tuesday",
                         "rce", "remote code execution", "buffer overflow", "poc"],
    "Data Breach":      ["data breach", "breach", "leak", "credential theft"],
    "Malware":          ["malware", "backdoor", "botnet", "spyware", "wiper", "c2"],
    "ICS / OT":         ["ics", "scada", "ot security", "critical infrastructure"],
    "Phishing":         ["phishing", "spear phishing", "smishing"],
    "Law Enforcement":  ["indictment", "arrest", "fbi", "takedown", "law enforcement"],
    "Advisory":         ["cisa", "ncsc", "us-cert", "advisory", "patch"],
}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][\w\-]*", text.lower())


def bm25_score(text: str, k1: float = 1.5, b: float = 0.75, avg_dl: float = 150) -> float:
    tokens = tokenize(text)
    dl = len(tokens)
    tf_map = Counter(tokens)
    score = 0.0

    for phrase, weight in KEYWORDS.items():
        phrase_tokens = phrase.split()
        if len(phrase_tokens) == 1:
            tf = tf_map.get(phrase_tokens[0], 0)
        else:
            tf = text.lower().count(phrase)

        if tf > 0:
            idf = math.log((1 + 1) / (1 + tf) + 1)  # simplified IDF
            tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg_dl))
            score += weight * idf * tf_norm

    return score


def detect_categories(text: str) -> list[str]:
    text_lower = text.lower()
    cats = []
    for cat, phrases in CATEGORY_TAGS.items():
        if any(p in text_lower for p in phrases):
            cats.append(cat)
    return cats or ["General"]


def has_critical_theme(text: str) -> bool:
    text_lower = text.lower()
    return any(theme in text_lower for theme in CRITICAL_THEMES)


def normalize_scores(items: list[dict]) -> list[dict]:
    scores = [i["raw_score"] for i in items if i["raw_score"] > 0]
    if not scores:
        return items
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    std = math.sqrt(variance) if variance > 0 else 1
    threshold = mean + 1.5 * std

    for item in items:
        raw = item["raw_score"]
        if std > 0:
            normalized = min(100, max(0, int(((raw - mean) / std) * 15 + 50)))
        else:
            normalized = 50
        item["score"] = normalized
        item["is_relevant"] = normalized >= 50 or item.get("critical", False)
        item["threshold"] = round(threshold, 2)

    return items
