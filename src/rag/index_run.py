import json
from datetime import date

from src.config import settings
from src.data.db import connect, init_db
from src.rag.embedding import embed_text

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def _insert_document(con, doc_type: str, source: str, content: str, created_at: str) -> int:
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO rag_documents (doc_type, source, content, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (doc_type, source, content, created_at),
    )
    return int(cur.lastrowid)

def _upsert_embedding(con, doc_id: int, model: str, vec) -> None:
    vec_bytes = vec.tobytes()
    dim = int(vec.shape[0])

    con.execute(
        """
        INSERT INTO rag_embeddings (doc_id, model, dim, vector)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(doc_id) DO UPDATE SET
          model = excluded.model,
          dim = excluded.dim,
          vector = excluded.vector
        """,
        (doc_id, model, dim, vec_bytes),
    )

def build_run_summary(analysis: dict, recommendations_text: str) -> str:
    mode = analysis.get("mode")
    window_days = analysis.get("window_days")
    actions_c = analysis.get("campaign_actions", [])
    actions_s = analysis.get("search_term_actions", [])

    top_campaigns = []
    for a in actions_c[:8]:
        top_campaigns.append(f"- {a.get('type')}: {a.get('campaign')} (cost={a.get('cost')}, conv={a.get('conversions')}, roas={a.get('roas')})")

    top_terms = []
    for a in actions_s[:8]:
        top_terms.append(f"- {a.get('type')}: {a.get('search_term')} (clicks={a.get('clicks')}, cost={a.get('cost')})")

    rec_head = recommendations_text.strip().splitlines()[:40]
    rec_head_text = "\n".join(rec_head)

    return f"""RUN SUMMARY
date: {date.today().isoformat()}
mode: {mode}
window_days: {window_days}

campaign_actions: {len(actions_c)}
search_term_actions: {len(actions_s)}

TOP CAMPAIGN ACTIONS
{chr(10).join(top_campaigns) if top_campaigns else "- (none)"}

TOP SEARCH TERM ACTIONS
{chr(10).join(top_terms) if top_terms else "- (none)"}

RECOMMENDATIONS (first 40 lines)
{rec_head_text}
"""

def main():
    init_db()

    analysis_path = settings.repo_root / "analysis_output.json"
    if not analysis_path.exists():
        raise FileNotFoundError(f"Missing {analysis_path}. Run analysis first.")

    reports = sorted(settings.reports_dir.glob("recommendations_*.md"), reverse=True)
    if not reports:
        raise FileNotFoundError(f"No recommendations found in {settings.reports_dir}. Run llm_recommender first.")
    rec_path = reports[0]

    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    rec_text = rec_path.read_text(encoding="utf-8")

    run_summary = build_run_summary(analysis, rec_text)
    created_at = date.today().isoformat()

    with connect() as con:
        analysis_doc_id = _insert_document(con, "analysis", str(analysis_path), json.dumps(analysis, ensure_ascii=False, indent=2), created_at)
        _upsert_embedding(con, analysis_doc_id, EMBED_MODEL, embed_text(run_summary, EMBED_MODEL))

        rec_doc_id = _insert_document(con, "recommendations", str(rec_path), rec_text, created_at)
        _upsert_embedding(con, rec_doc_id, EMBED_MODEL, embed_text(rec_text[:8000], EMBED_MODEL))

        summary_doc_id = _insert_document(con, "run_summary", f"run:{created_at}", run_summary, created_at)
        _upsert_embedding(con, summary_doc_id, EMBED_MODEL, embed_text(run_summary, EMBED_MODEL))

        con.commit()

    print(f"Indexed run into RAG: analysis={analysis_doc_id}, recommendations={rec_doc_id}, summary={summary_doc_id}")

if __name__ == "__main__":
    main()
