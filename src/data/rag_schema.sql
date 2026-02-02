CREATE TABLE IF NOT EXISTS rag_documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  doc_type TEXT NOT NULL,                 -- "analysis", "recommendations", "run_summary"
  source TEXT NOT NULL,                   -- filename/path or logical id
  content TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rag_embeddings (
  doc_id INTEGER PRIMARY KEY,
  model TEXT NOT NULL,
  dim INTEGER NOT NULL,
  vector BLOB NOT NULL,
  FOREIGN KEY (doc_id) REFERENCES rag_documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rag_documents_type_time
ON rag_documents(doc_type, created_at);
