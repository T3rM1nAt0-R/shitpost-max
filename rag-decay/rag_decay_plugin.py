import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from harness.shitpost_base import Shitpost


class RagDecayPlugin(Shitpost):
    """Daily tick to measure retrieval quality of a RAG pipeline."""

    name = "rag-decay"
    internal = False
    commit_template = "rag-decay: R@5={avg_recall@5:.2f}, P@5={avg_precision@5:.2f}, MRR={avg_MRR:.2f}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "rag_decay_state.json"
        self._test_set_path = os.path.join(self._plugin_dir(), "test_set.json")
        self._top_k = int(os.getenv("TOP_K", 5))
        self._rag_endpoint = os.getenv("RAG_ENDPOINT", "http://localhost:8000/retrieve")

    def _load_state(self, plugin_dir: str) -> Dict[str, any]:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: rag-decay state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"queries_run", "queries_with_zero_recall"}
            if not required.issubset(state.keys()):
                print(
                    "warning: rag-decay state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> Dict[str, any]:
        return {
            "queries_run": 0,
            "queries_with_zero_recall": 0,
        }

    def _save_state(self, plugin_dir: str, state: Dict[str, any]) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _load_test_set(self) -> List[Dict[str, any]]:
        """Load the test set of queries and ground-truth relevant chunk IDs."""
        with open(self._test_set_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _compute_metrics(
        retrieved_ids: List[str], relevant_ids: List[str]
    ) -> Tuple[float, float, float]:
        """Compute recall@K, precision@K, and MRR for K=5."""
        if not retrieved_ids:
            return 0.0, 0.0, 0.0

        relevant_set = set(relevant_ids)
        retrieved_set = set(retrieved_ids[:5])

        recall_at_5 = len(relevant_set.intersection(retrieved_set)) / len(relevant_set)
        precision_at_5 = len(relevant_set.intersection(retrieved_set)) / len(retrieved_set)
        mrr = 0.0
        for rank, chunk_id in enumerate(retrieved_ids[:5], start=1):
            if chunk_id in relevant_set:
                mrr = 1.0 / rank
                break

        return recall_at_5, precision_at_5, mrr

    def produce(self) -> Dict[str, any]:
        """Run all queries against the RAG pipeline and compute metrics."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        test_set = self._load_test_set()

        results = []
        for query_id, query_data in enumerate(test_set, start=1):
            response = None
            try:
                response = requests.post(
                    self._rag_endpoint,
                    json={"query": query_data["query"], "top_k": self._top_k},
                    timeout=30,
                )
                response.raise_for_status()
                retrieved_ids = [item["id"] for item in response.json()["chunks"]]
            except (requests.RequestException, KeyError) as exc:
                print(f"warning: failed to retrieve chunks for query {query_id}: {exc}", file=sys.stderr)
                retrieved_ids = []

            relevant_ids = query_data["relevant_chunk_ids"]
            recall_at_5, precision_at_5, mrr = self._compute_metrics(retrieved_ids, relevant_ids)

            results.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "query_id": query_id,
                "query": query_data["query"],
                "retrieved_ids": retrieved_ids,
                "relevant_ids": relevant_ids,
                "recall@5": recall_at_5,
                "precision@5": precision_at_5,
                "MRR": mrr,
            })

            if not retrieved_ids:
                state["queries_with_zero_recall"] += 1

        avg_recall_at_5 = sum(result["recall@5"] for result in results) / len(results)
        avg_precision_at_5 = sum(result["precision@5"] for result in results) / len(results)
        avg_mrr = sum(result["MRR"] for result in results) / len(results)

        state["queries_run"] += len(results)

        self._save_state(plugin_dir, state)

        return {
            "avg_recall@5": avg_recall_at_5,
            "avg_precision@5": avg_precision_at_5,
            "avg_MRR": avg_mrr,
            "results": results,
        }
