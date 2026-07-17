import glob
import os
import sys
import time
import urllib.request
import json

import psycopg2

CORPUS = "/home/niraj/atlas-docs/mind-junkyard/shitpost-max"
OLLAMA_URL = "http://localhost:1601/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
DB_DSN = "host=127.0.0.1 port=1502 dbname=rag user=rag password=rag"
MAX_CHUNK_CHARS = 2000


def embed(text: str) -> list:
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps({"model": EMBED_MODEL, "prompt": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["embedding"]


OVERLAP_RATIO = 0.15  # ~15% of MAX_CHUNK_CHARS carried into the next chunk


def _overlap_prefix(prev_chunk: str, max_chars: int) -> str:
    """Trailing paragraphs of prev_chunk, up to max_chars, so a fact split
    across a chunk boundary still appears whole in at least one chunk."""
    paras = [p for p in prev_chunk.split("\n\n") if p.strip()]
    carry, total = [], 0
    for p in reversed(paras):
        if total + len(p) > max_chars and carry:
            break
        carry.insert(0, p)
        total += len(p)
    return "\n\n".join(carry)


def chunk_file(path: str):
    text = open(path, encoding="utf-8", errors="ignore").read().strip()
    if not text:
        return []
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    overlap_budget = int(MAX_CHUNK_CHARS * OVERLAP_RATIO)
    chunks, buf = [], ""
    for p in paras:
        if len(buf) + len(p) > MAX_CHUNK_CHARS and buf:
            chunks.append(buf)
            buf = _overlap_prefix(buf, overlap_budget)
        buf = (buf + "\n\n" + p).strip()
    if buf:
        chunks.append(buf)
    return chunks


def main():
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS doc_chunks (
            id SERIAL PRIMARY KEY,
            file_path TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding vector(768)
        );
    """)
    cur.execute("TRUNCATE doc_chunks;")
    conn.commit()

    files = sorted(glob.glob(os.path.join(CORPUS, "**", "*.md"), recursive=True))
    print(f"found {len(files)} files")

    total_chunks = 0
    start = time.time()
    for i, path in enumerate(files):
        rel = os.path.relpath(path, CORPUS)
        chunks = chunk_file(path)
        for chunk in chunks:
            try:
                vec = embed(chunk)
            except Exception as e:
                print(f"embed failed for {rel}: {e}", file=sys.stderr)
                continue
            cur.execute(
                "INSERT INTO doc_chunks (file_path, content, embedding) VALUES (%s, %s, %s)",
                (rel, chunk, vec),
            )
            total_chunks += 1
        if (i + 1) % 50 == 0:
            conn.commit()
            elapsed = time.time() - start
            print(f"  {i+1}/{len(files)} files, {total_chunks} chunks, {elapsed:.0f}s elapsed")

    conn.commit()
    cur.execute("CREATE INDEX IF NOT EXISTS doc_chunks_embedding_idx ON doc_chunks USING hnsw (embedding vector_cosine_ops);")
    conn.commit()
    print(f"DONE: {total_chunks} chunks from {len(files)} files in {time.time()-start:.0f}s")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
