#!/usr/bin/env python3
"""Merge CT-discovered domains into known_ai_domains.json.

Reads data/ct_discoveries.json, appends new entries to
known_ai_domains.json, deduplicates by domain key (case-insensitive),
sorts alphabetically, and removes the discoveries file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
KNOWN_DOMAINS_FILE = DATA_DIR / "known_ai_domains.json"
CT_DISCOVERIES_FILE = DATA_DIR / "ct_discoveries.json"

_PROVIDER_MAP: dict[str, str] = {
    "openai.com": "OpenAI",
    "anthropic.com": "Anthropic",
    "googleapis.com": "Google",
    "microsoft.com": "Microsoft",
    "mistral.ai": "Mistral AI",
    "perplexity.ai": "Perplexity AI",
    "huggingface.co": "Hugging Face",
    "groq.com": "Groq",
    "replicate.com": "Replicate",
    "cohere.com": "Cohere",
    "together.ai": "Together AI",
    "stability.ai": "Stability AI",
    "x.ai": "xAI",
    "meta.ai": "Meta",
    "deepmind.com": "Google DeepMind",
    "ai21.com": "AI21 Labs",
    "amazon.com": "Amazon",
}


def infer_provider(source_domain: str) -> str:
    return _PROVIDER_MAP.get(source_domain, source_domain)


def main() -> int:
    if not CT_DISCOVERIES_FILE.exists():
        print("No ct_discoveries.json found — nothing to merge.")
        return 0

    discoveries: list[dict] = json.loads(CT_DISCOVERIES_FILE.read_text(encoding="utf-8"))
    if not discoveries:
        print("ct_discoveries.json is empty — nothing to merge.")
        CT_DISCOVERIES_FILE.unlink(missing_ok=True)
        return 0

    existing: list[dict] = json.loads(KNOWN_DOMAINS_FILE.read_text(encoding="utf-8"))
    existing_keys: set[str] = {d.get("domain", "").lower() for d in existing}

    new_count = 0
    for disc in discoveries:
        domain = disc.get("domain", "").lower()
        if not domain or domain in existing_keys:
            continue
        existing.append({
            "domain": domain,
            "provider": infer_provider(disc.get("source_domain", "")),
            "app": "",
            "risk": disc.get("risk", "medium"),
            "category": "Generative AI",
        })
        existing_keys.add(domain)
        new_count += 1

    # Deduplicate (case-insensitive) then sort
    seen: set[str] = set()
    deduped: list[dict] = []
    for entry in existing:
        key = entry.get("domain", "").lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(entry)

    deduped.sort(key=lambda d: d.get("domain", "").lower())

    KNOWN_DOMAINS_FILE.write_text(
        json.dumps(deduped, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    CT_DISCOVERIES_FILE.unlink(missing_ok=True)

    print(f"Merged {new_count} new domains. Total: {len(deduped)} domains.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
