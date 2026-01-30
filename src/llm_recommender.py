import json
import subprocess
import shutil
from pathlib import Path
from datetime import date

MODEL = "llama3:8b"

ANALYSIS_FILE = Path("analysis_output.json")
REPORTS_DIR = Path("reports")

def build_prompt(analysis: dict) -> str:
    analysis_json = json.dumps(analysis, indent=2, ensure_ascii=False)
    window_days = analysis.get("window_days", 7)

    return f"""
You are a senior Google Ads performance consultant with deep experience in
Search campaigns for affiliate offers (Clickbank, BuyGoods, MaxWeb).

Context:
- Campaign type: Search only
- Objective: Maximize ROAS (not volume)
- Decision window: {window_days} days
- Account type: Affiliate offers
- Budgets are limited; capital preservation is important.
- All metrics were pre-calculated. Do NOT calculate metrics again.

Rules:
- Do NOT suggest automation or API-based changes.
- Do NOT suggest smart bidding changes.
- Avoid generic advice (e.g., “monitor closely”, “optimize targeting”).
- Be concrete and conservative.
- Assume execution is manual in Google Ads UI.

Input data (JSON):
{analysis_json}

Your task:
1. Prioritize actions (High / Medium / Low) based on expected ROAS impact.
2. For each action, explain WHY it matters using the data provided.
3. Explain HOW to execute it step-by-step inside Google Ads UI.
4. For each action, define:
   - What could go wrong
   - A clear validation metric (e.g., ROAS >= X after 7 days)

Output requirements:
- Clear sections
- Bullet points
- Action-oriented language
- No marketing fluff

Final instruction:
- The analysis must be done in English internally,
  but the final answer must be written just in clear Brazilian Portuguese (pt-BR).
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
        timeout=600,
    )

    if result.returncode != 0:
        raise RuntimeError(f"LLM error: {result.stderr}")

    return result.stdout

def main():
    if not ANALYSIS_FILE.exists():
        raise FileNotFoundError(f"Missing {ANALYSIS_FILE}. Generate it first (analysis_rules).")

    analysis = json.loads(ANALYSIS_FILE.read_text(encoding="utf-8"))
    prompt = build_prompt(analysis)
    response = run_llm(prompt)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"recommendations_{date.today().isoformat()}.txt"
    out_path.write_text(response, encoding="utf-8")

    print("\n===== LLM RECOMMENDATIONS =====\n")
    print(response)
    print(f"\nSaved report to: {out_path.resolve()}")

if __name__ == "__main__":
    main()
