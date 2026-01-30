import subprocess
import sys
from pathlib import Path

PYTHON = sys.executable
ROOT = Path(__file__).resolve().parents[1]

def run_step(name: str, cmd: list[str]):
    print(f"\n=== {name} ===")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {name}")

def main():
    run_step("Sync client accounts", [PYTHON, "-m", "src.sync_client_accounts"])
    run_step("Fetch daily metrics", [PYTHON, "-m", "src.fetch_daily_metrics"])
    run_step("Fetch search terms", [PYTHON, "-m", "src.fetch_search_terms"])
    run_step("Run analysis rules", [PYTHON, "-m", "src.analysis_rules"])
    run_step("Run LLM recommender", [PYTHON, "-m", "src.llm_recommender"])
    print("\n✅ DONE")

if __name__ == "__main__":
    main()
