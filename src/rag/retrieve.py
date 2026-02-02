import numpy as np
from src.data.db import connect
from src.rag.embedding import embed_text, cosine_sim

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def _blob_to_vec(blob: bytes, dim: int) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32, count=dim)

def retrieve_context(query: str, top_k: int = 5, doc_types: tuple[str, ...] = ("run_summary", "recommendations")) -> list[dict]:
    qv = embed_text(query, EMBED_MODEL)

    with connect() as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT d.id, d.doc_type, d.source, d.content, d.created_at,
                   e.dim, e.vector
            FROM rag_documents d
            JOIN rag_embeddings e ON e.doc_id = d.id
            WHERE d.doc_type IN ({})
            ORDER BY d.created_at DESC
            LIMIT 200
            """.format(",".join("?" for _ in doc_types)),
            doc_types,
        )

        scored = []
        for doc_id, doc_type, source, content, created_at, dim, blob in cur.fetchall():
            dv = _blob_to_vec(blob, int(dim))
            score = cosine_sim(qv, dv)
            scored.append((score, doc_id, doc_type, source, content, created_at))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, doc_id, doc_type, source, content, created_at in scored[:top_k]:
        out.append(
            {
                "score": round(float(score), 4),
                "doc_id": doc_id,
                "doc_type": doc_type,
                "source": source,
                "created_at": created_at,
                "content": content[:2500],
            }
        )
    return out
