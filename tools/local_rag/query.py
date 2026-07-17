import sys
import json
import urllib.request

import psycopg2

OLLAMA_URL = "http://localhost:1601/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
DB_DSN = "host=127.0.0.1 port=1502 dbname=rag user=rag password=rag"
CHAT_URL = "http://localhost:1601/api/generate"
CHAT_MODEL = "qwen2.5-coder:7b-instruct-q6_K"
TOP_K = 5
CANDIDATE_K = 20
RERANK_SNIPPET_CHARS = 400


def embed(text: str) -> list:
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps({"model": EMBED_MODEL, "prompt": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["embedding"]


def retrieve(question: str, k: int = CANDIDATE_K):
    vec = embed(question)
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    cur.execute(
        "SELECT file_path, content, 1 - (embedding <=> %s::vector) AS similarity "
        "FROM doc_chunks ORDER BY embedding <=> %s::vector LIMIT %s",
        (vec, vec, k),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def _ollama_generate(prompt: str, timeout: int = 60) -> str:
    req = urllib.request.Request(
        CHAT_URL,
        data=json.dumps({"model": CHAT_MODEL, "prompt": prompt, "stream": False}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())["response"]


def rerank(question: str, candidates, top_k: int = TOP_K):
    """Re-score vector-similarity candidates for actual relevance via one extra local LLM call.

    Falls back to the original vector-similarity order (just truncated to top_k)
    if the model's response doesn't parse into a clean list of indices -- a
    malformed rerank response should never break retrieval.
    """
    if len(candidates) <= top_k:
        return candidates

    listing = "\n\n".join(
        f"[{i}] ({fp})\n{content[:RERANK_SNIPPET_CHARS]}"
        for i, (fp, content, _sim) in enumerate(candidates)
    )
    prompt = (
        f"Question: {question}\n\n"
        f"Below are {len(candidates)} candidate passages, numbered [0]-[{len(candidates)-1}]. "
        f"Pick the {top_k} MOST RELEVANT to answering the question, ordered best-first.\n"
        f"Respond with ONLY a comma-separated list of indices, nothing else. Example: 3,0,7,1,12\n\n"
        f"{listing}"
    )
    try:
        raw = _ollama_generate(prompt, timeout=180).strip()
        indices = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
        indices = [i for i in indices if 0 <= i < len(candidates)]
        # dedupe while preserving order
        seen = set()
        ordered = [i for i in indices if not (i in seen or seen.add(i))]
        if len(ordered) < top_k:
            raise ValueError(f"only parsed {len(ordered)} valid indices, need {top_k}")
        return [candidates[i] for i in ordered[:top_k]]
    except Exception as e:
        print(f"warning: rerank failed ({e}), falling back to vector-similarity order", file=sys.stderr)
        return candidates[:top_k]


def generate_answer(question: str, chunks):
    context = "\n\n---\n\n".join(f"[{fp}]\n{content}" for fp, content, _ in chunks)
    prompt = (
        "Answer the question using ONLY the context below. If the context doesn't "
        "contain the answer, say so explicitly.\n\n"
        f"CONTEXT:\n{context}\n\nQUESTION: {question}\n\nANSWER:"
    )
    req = urllib.request.Request(
        CHAT_URL,
        data=json.dumps({"model": CHAT_MODEL, "prompt": prompt, "stream": False}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=240) as resp:
        return json.loads(resp.read())["response"]


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "Why were reddit-titles and spotify-charts retired?"
    candidates = retrieve(question)
    print(f"=== {len(candidates)} CANDIDATES (vector similarity) for: {question!r} ===")
    for fp, content, sim in candidates:
        print(f"  [{sim:.3f}] {fp}")

    chunks = rerank(question, candidates)
    print(f"\n=== TOP {len(chunks)} AFTER RERANK ===")
    for fp, content, sim in chunks:
        print(f"  [{sim:.3f}] {fp}")
    print()
    print("=== ANSWER ===")
    print(generate_answer(question, chunks))
