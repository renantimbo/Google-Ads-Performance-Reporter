import json
import subprocess
import shutil
from datetime import date
from pathlib import Path

from src.config import settings
from src.rag.retrieve import retrieve_context

MODEL = "llama3:8b"
ANALYSIS_FILE = settings.repo_root / "analysis_output.json"

RAG_TOP_K = 5
RAG_MAX_CHARS = 6000
RAG_QUERY = "weekly google ads optimization decisions roas winners losers negatives"


def _format_rag_context(items: list[dict]) -> str:
    """Format retrieved RAG docs into a compact context block for the prompt."""
    if not items:
        return "No past context found (first run or memory not indexed yet)."

    chunks = []
    total = 0
    for c in items:
        header = f"[{c.get('doc_type')} | {c.get('created_at')} | score={c.get('score')}]"
        body = (c.get("content") or "").strip()
        block = f"{header}\n{body}\n"

        if total + len(block) > RAG_MAX_CHARS:
            remaining = max(0, RAG_MAX_CHARS - total)
            if remaining > 200:
                chunks.append(block[:remaining] + "\n[...truncated...]\n")
            break

        chunks.append(block)
        total += len(block)

    return "\n".join(chunks).strip()


def build_prompt(analysis: dict, rag_context: str) -> str:
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

Memory rules (RAG context):
- You will receive past runs (summaries/recommendations).
- Do NOT repeat the exact same recommendation if it was attempted recently and failed.
- If you repeat a recommendation, explain WHY it still makes sense now.
- Prefer consistency with past decisions unless current data strongly contradicts them.

Past context (RAG results):
{rag_context}

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

    try:
        items = retrieve_context(query=RAG_QUERY, top_k=RAG_TOP_K)
        rag_context = _format_rag_context(items)
    except Exception as e:
        rag_context = f"RAG retrieval failed: {e}"

    prompt = build_prompt(analysis, rag_context)
    response = run_llm(prompt)

    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    out_md = settings.reports_dir / f"recommendations_{date.today().isoformat()}.md"
    out_md.write_text(response + "\n", encoding="utf-8")

    print("\n===== LLM RECOMMENDATIONS =====\n")
    print(response)
    print(f"\nSaved report to: {out_md.resolve()}")

    # Optional: automatically index this run into memory after generating the report.
    # Recommended to call indexing from run_all.py, but this helps when running llm_recommender alone.
    # Uncomment if you want auto-index here:
    #
    # from src.rag.index_run import main as index_main
    # index_main()


if __name__ == "__main__":
    main()
