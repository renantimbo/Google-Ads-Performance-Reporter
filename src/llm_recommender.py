import json
import subprocess
import shutil
from datetime import date
from pathlib import Path

from src.config import settings

MODEL = "llama3:8b"

ANALYSIS_FILE = settings.repo_root / "analysis_output.json"


def build_prompt(analysis: dict) -> str:
    analysis_json = json.dumps(analysis, indent=2)

    window_days = analysis.get("window_days", 7)
    thresholds = analysis.get("thresholds", {})
    losers = thresholds.get("campaign_losers", {})
    winners = thresholds.get("campaign_winners", {})

    lose_min_cost = losers.get("min_cost", 300.0)
    win_min_roas = winners.get("min_roas", 1.2)
    win_min_conv = winners.get("min_conversions", 2)
    win_min_cost = winners.get("min_cost", 200.0)

    return f"""
You are a senior Google Ads performance consultant specialized in Search campaigns
for affiliate offers (Clickbank, BuyGoods, MaxWeb).

You are conservative, data-driven, and operationally realistic.
Assume all actions are executed manually in the Google Ads UI.

Context:
- Campaign type: Search only
- Objective: Maximize ROAS (capital preservation > scale)
- Decision window: {window_days} days
- All metrics were pre-calculated. DO NOT recalculate metrics.

Hard constraints:
- Do NOT suggest automation, scripts, API usage, or smart bidding changes.
- Do NOT provide generic advice.
- Do NOT invent features or UI elements that do not exist in Google Ads.

STRICT prioritization rules:
1) Any campaign with cost >= {lose_min_cost} AND conversions = 0 MUST be HIGH priority.
2) Any campaign with ROAS >= {win_min_roas}, conversions >= {win_min_conv},
   and cost >= {win_min_cost} MUST be HIGH or MEDIUM priority.
3) LOW priority is ONLY for low-spend or informational items.

Completeness rules:
- You MUST cover ALL items from:
  - campaign_actions
  - search_term_actions
- You MUST provide a detailed section for EACH item.
- You are NOT allowed to use placeholders or omit actions.

Output format (MANDATORY — follow exactly):

# Priority Summary
## High
- ...
## Medium
- ...
## Low
- ...

# Action Details
## [ITEM NAME]
- Type: (Scale winner | Pause / Restructure | Add negative keyword)
- Why it matters (cite cost, conversions, ROAS from the data):
- How to execute in Google Ads UI (step by step):
  1) ...
  2) ...
  3) ...
- Risks (realistic, not generic):
- Validation metric (after {window_days} days):

Input data (JSON):
{analysis_json}
""".strip()

def run_llm(prompt: str) -> str:
    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        raise RuntimeError("Ollama not found in PATH. Ensure ollama is installed and available.")

    result = subprocess.run(
        [ollama_bin, "run", MODEL],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )

    if result.returncode != 0:
        raise RuntimeError(f"LLM error: {result.stderr}")

    return result.stdout.strip()


def main():
    if not ANALYSIS_FILE.exists():
        raise FileNotFoundError(
            f"Missing {ANALYSIS_FILE}. Generate it first (python -m src.analysis_rules)."
        )

    analysis = json.loads(ANALYSIS_FILE.read_text(encoding="utf-8"))
    prompt = build_prompt(analysis)
    response = run_llm(prompt)

    settings.reports_dir.mkdir(parents=True, exist_ok=True)

    out_md = settings.reports_dir / f"recommendations_{date.today().isoformat()}.md"
    out_md.write_text(response + "\n", encoding="utf-8")

    print("\n===== LLM RECOMMENDATIONS =====\n")
    print(response)
    print(f"\nSaved report to: {out_md.resolve()}")


if __name__ == "__main__":
    main()
