# ai-llm-domains

[![CT Log Scan](https://github.com/repins267/ai-llm-domains/actions/workflows/ct-scan.yml/badge.svg)](https://github.com/repins267/ai-llm-domains/actions/workflows/ct-scan.yml)

A maintained reference dataset of AI/LLM domains, applications, proxy categories,
and DLP alert patterns for use with [exa-tools](https://github.com/repins267/exa-tools)
and Exabeam New-Scale context tables.

---

## Contents

| File | Description |
|---|---|
| `data/known_ai_domains.json` | AI/LLM domains with provider, risk, and category metadata |
| `data/known_ai_apps.json` | AI application names and aliases for context table matching |
| `data/known_proxy_categories.json` | Vendor-specific proxy/URL filter categories for AI/LLM traffic |
| `data/known_dlp_alert_patterns.json` | DLP ruleset/alert names that indicate AI data exfiltration |

---

## Data Schemas

### known_ai_domains.json

```json
{
  "domain":   "chatgpt.com",        // Fully-qualified domain name (the lookup key)
  "provider": "OpenAI",             // Vendor / provider name
  "app":      "ChatGPT",            // Associated application (blank for infra/API domains)
  "risk":     "medium",             // "low" | "medium" | "high" | "critical"
  "category": "Generative AI",      // Functional category
  "type":     "primary",            // "primary" | "api" | "cdn" | "infra" (optional)
  "notes":    "..."                 // Human-readable notes (optional)
}
```

**Risk levels:**
| Level | Meaning |
|---|---|
| `low` | Informational / observability only |
| `medium` | Default — monitor and alert on anomalous volume |
| `high` | Sensitive data transfer risk; consider blocking for regulated users |
| `critical` | Known policy violation or data exfiltration vector |

### known_ai_apps.json

```json
{
  "app":      "ChatGPT",
  "provider": "OpenAI",
  "aliases":  ["chatgpt", "gpt-4", "gpt4"],   // Search aliases for log matching
  "risk":     "medium",
  "category": "Generative AI"
}
```

### known_proxy_categories.json

```json
{
  "category": "Generative AI",       // Exact category name as it appears in the vendor product
  "vendor":   "Zscaler",             // Proxy/CASB/SWG vendor
  "notes":    "..."
}
```

### known_dlp_alert_patterns.json

```json
{
  "pattern":     "AI Data Upload",   // Alert name / ruleset name
  "vendor":      "Zscaler",          // DLP vendor
  "description": "...",
  "risk":        "high"
}
```

---

## CT Log Scanning

A GitHub Actions workflow runs every Monday at 06:00 UTC and:

1. Queries [crt.sh](https://crt.sh) for TLS certificates issued in the last 7 days
   for 17 known AI provider base domains (OpenAI, Anthropic, Google, Microsoft, etc.)
2. Extracts all unique subdomains from `name_value` fields
3. Diffs against `known_ai_domains.json`
4. If new domains are found, opens a pull request with the candidates

**Provider domains scanned:**
`openai.com`, `anthropic.com`, `googleapis.com`, `microsoft.com`, `mistral.ai`,
`perplexity.ai`, `huggingface.co`, `groq.com`, `replicate.com`, `cohere.com`,
`together.ai`, `stability.ai`, `x.ai`, `meta.ai`, `deepmind.com`, `ai21.com`,
`amazon.com`

You can also trigger a scan manually from the **Actions** tab → **CT Log Scanner** →
**Run workflow**.

---

## Adding Domains Manually

1. Edit `data/known_ai_domains.json`
2. Add your entry following the schema above — include `provider`, `risk`, and `category`
3. Open a PR with the source cited in the PR description (e.g., vendor announcement,
   Shodan, VirusTotal passive DNS)

Keep entries sorted alphabetically by `domain`.

---

## How exa-tools Consumes This Repo

`exa update` clones/pulls this repo into `~/.exa/aillm-domains/`. When
`exa aillm sync` (or any command calling `load_reference_data()`) runs,
it checks for `~/.exa/aillm-domains/data/` first. If present, those files
take precedence over the bundled snapshot inside the exa-tools package,
so you always get the latest curated data without needing to upgrade the
package.

```bash
exa update          # pull latest data including this repo
exa aillm sync      # sync to Exabeam context tables using current data
exa aillm status    # show record counts vs. reference counts
```

---

## Roadmap

### Applications (known_ai_apps.json)
Weekly scraper against Futurepedia and Product Hunt AI category — diffs
new app names against the known list and opens a PR for review. Highest
priority: new AI tools launch daily and this list drifts fastest.

### Proxy & Web Categories (known_proxy_categories.json)
Quarterly monitor against Zscaler and Palo Alto URL filtering release
notes for new AI/LLM category additions. Low frequency — proxy vendors
update AI categories a few times per year.

### DLP Rulesets (known_dlp_alert_patterns.json)
Manual quarterly review against Microsoft Purview, Symantec DLP, and
Forcepoint release notes for new AI-specific policy templates. Changes
infrequently enough that automation adds little value here.

### All workflows follow the same pattern
Scraper runs on a schedule → diffs against known list → opens a PR with
additions tagged by source → human reviews and merges →
sync-to-exa-tools.yml propagates the update to the bundled fallback in
exa-tools automatically.

---

## License

Reference data compiled from public sources. CC0 1.0 — no rights reserved.
