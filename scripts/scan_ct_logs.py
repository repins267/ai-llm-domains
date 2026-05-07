#!/usr/bin/env python3
"""Scan Certificate Transparency logs for new AI/LLM subdomains.

Checks crt.sh for certificates issued in the last 7 days for known
AI/LLM provider base domains. Compares against known_ai_domains.json
and writes new candidates to data/ct_discoveries.json.

Exit codes:
  0 — no new domains found
  1 — new domains found (CI should trigger merge + PR)
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

PROVIDER_DOMAINS: list[str] = [
    "openai.com",
    "anthropic.com",
    "googleapis.com",
    "microsoft.com",
    "mistral.ai",
    "perplexity.ai",
    "huggingface.co",
    "groq.com",
    "replicate.com",
    "cohere.com",
    "together.ai",
    "stability.ai",
    "x.ai",
    "meta.ai",
    "deepmind.com",
    "ai21.com",
    "amazon.com",
]

DATA_DIR = Path(__file__).parent.parent / "data"
KNOWN_DOMAINS_FILE = DATA_DIR / "known_ai_domains.json"
CT_DISCOVERIES_FILE = DATA_DIR / "ct_discoveries.json"
LOOKBACK_DAYS = 7


def fetch_ct_entries(domain: str, client: httpx.Client) -> list[dict]:
    """Fetch recent CT log entries for a domain from crt.sh."""
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    try:
        resp = client.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        print(f"  WARN: crt.sh query failed for {domain}: {exc}", file=sys.stderr)
        return []


def parse_not_before(entry: dict) -> datetime | None:
    """Parse the not_before timestamp from a crt.sh entry."""
    raw = (entry.get("not_before") or "")[:19]
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt[:len(raw)]).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def extract_hostnames(name_value: str) -> list[str]:
    """Extract individual hostnames from a cert name_value field."""
    names: list[str] = []
    for part in name_value.replace("\n", ",").split(","):
        part = part.strip().lower()
        # Skip wildcards; require at least one dot
        if part and not part.startswith("*") and "." in part:
            names.append(part)
    return names


def load_known_keys() -> set[str]:
    """Return the set of lowercase domain keys from known_ai_domains.json."""
    if not KNOWN_DOMAINS_FILE.exists():
        return set()
    data: list[dict] = json.loads(KNOWN_DOMAINS_FILE.read_text(encoding="utf-8"))
    return {d.get("domain", "").lower() for d in data if d.get("domain")}


def scan_provider(domain: str, cutoff: datetime, client: httpx.Client) -> list[str]:
    """Return deduplicated subdomains seen in CT logs since cutoff."""
    entries = fetch_ct_entries(domain, client)
    seen: set[str] = set()
    for entry in entries:
        nb = parse_not_before(entry)
        if nb and nb >= cutoff:
            for hostname in extract_hostnames(entry.get("name_value", "")):
                if hostname == domain or hostname.endswith(f".{domain}"):
                    seen.add(hostname)
    return sorted(seen)


def main() -> int:
    cutoff = datetime.now(UTC) - timedelta(days=LOOKBACK_DAYS)
    known = load_known_keys()
    today = datetime.now(UTC).date().isoformat()
    discoveries: list[dict] = []

    print(f"Scanning {len(PROVIDER_DOMAINS)} provider domains (last {LOOKBACK_DAYS} days)...")

    with httpx.Client(follow_redirects=True) as client:
        for domain in PROVIDER_DOMAINS:
            print(f"  {domain} ...", end=" ", flush=True)
            found = scan_provider(domain, cutoff, client)
            new = [h for h in found if h not in known]
            print(f"{len(new)} new")
            for hostname in new:
                discoveries.append({
                    "domain": hostname,
                    "source_domain": domain,
                    "first_seen": today,
                    "risk": "medium",
                })

    if not discoveries:
        print("\nNo new domains found.")
        return 0

    providers = sorted({d["source_domain"] for d in discoveries})
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CT_DISCOVERIES_FILE.write_text(
        json.dumps(discoveries, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n{len(discoveries)} new domains discovered across {len(providers)} providers.")
    print(f"Written to {CT_DISCOVERIES_FILE.name}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
