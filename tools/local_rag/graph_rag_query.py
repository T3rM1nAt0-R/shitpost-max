import re
import subprocess
import sys

from query import retrieve, rerank, generate_answer, CANDIDATE_K, TOP_K

GRAPHIFY_ROOT = "/home/niraj/atlas-docs"
GRAPHIFY_CORPUS_PREFIX = "shitpost-max/"  # source_file paths are relative to atlas-docs root


def graph_neighborhood(question: str, budget: int = 1500) -> set:
    """Run graphify query and return the set of source_file basenames it surfaced."""
    try:
        result = subprocess.run(
            ["graphify", "query", question, "--budget", str(budget)],
            cwd=GRAPHIFY_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"warning: graphify query failed ({e}); continuing with vector-only retrieval", file=sys.stderr)
        return set()

    files = set()
    for m in re.finditer(r"\[src=([^\]\s]+)", result.stdout):
        src = m.group(1)
        if src == "None":
            continue
        # doc_chunks.file_path is relative to mind-junkyard/shitpost-max/; graphify's
        # src= is relative to atlas-docs root and may be prefixed with graphify-out-cycle/*
        # or similar bookkeeping directories from earlier merges -- normalize to the
        # trailing "<plugin>/<file>.md" shape both sides actually share.
        parts = src.split("/")
        if len(parts) >= 2:
            files.add("/".join(parts[-2:]))
    return files


def graph_boosted_retrieve(question: str, k: int = CANDIDATE_K):
    """Graph traversal is the PRIMARY filter when it finds a neighborhood --
    those chunks are placed first (so reranking sees them ahead of pure
    vector-similarity noise), with vector search unioned in after as the
    supplement/fallback. If graphify finds nothing (or fails), vector search
    alone is the whole result -- same graceful-degradation behavior as before,
    just inverted priority when both are available.
    """
    vector_candidates = retrieve(question, k=k)
    neighborhood = graph_neighborhood(question)

    if not neighborhood:
        return vector_candidates, neighborhood

    from query import embed, DB_DSN
    import psycopg2

    vec = embed(question)
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    graph_first = []
    for file_path in neighborhood:
        cur.execute(
            "SELECT file_path, content, 1 - (embedding <=> %s::vector) AS similarity "
            "FROM doc_chunks WHERE file_path = %s ORDER BY embedding <=> %s::vector LIMIT 2",
            (vec, file_path, vec),
        )
        graph_first.extend(cur.fetchall())
    cur.close()
    conn.close()

    # Graph-sourced chunks first (primary), vector-only chunks appended after
    # (supplement) -- reranking sees graph-connected material ahead of
    # plain-similarity noise instead of the two being interleaved by score.
    seen = {(fp, content) for fp, content, _ in graph_first}
    combined = list(graph_first)
    for fp, content, sim in vector_candidates:
        if (fp, content) not in seen:
            combined.append((fp, content, sim))
            seen.add((fp, content))
    return combined, neighborhood


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "Why were reddit-titles and spotify-charts retired?"

    combined, neighborhood = graph_boosted_retrieve(question)
    print(f"=== graphify neighborhood: {len(neighborhood)} file(s) ===")
    for f in sorted(neighborhood):
        print(f"  {f}")

    print(f"\n=== {len(combined)} CANDIDATES (vector + graph-boosted) ===")
    for fp, content, sim in combined:
        print(f"  [{sim:.3f}] {fp}")

    chunks = rerank(question, combined, top_k=TOP_K)
    print(f"\n=== TOP {len(chunks)} AFTER RERANK ===")
    for fp, content, sim in chunks:
        print(f"  [{sim:.3f}] {fp}")

    print()
    print("=== ANSWER ===")
    print(generate_answer(question, chunks))
