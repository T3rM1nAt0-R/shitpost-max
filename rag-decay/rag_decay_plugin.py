"""Measures how badly my RAG pipeline forgets things over time, so I can watch knowledge rot in real time. Very zen."""

import json
import os
import sys
from datetime import datetime, timezone

import requests
from typing import Dict, List, Tuple

from harness.shitpost_base import Shitpost


class RagDecayPlugin(Shitpost):
    """Daily tick to measure retrieval quality of a RAG pipeline."""

    name = "rag-decay"
    internal = False
    commit_template = "rag-decay: R@5={avg_recall@5:.2f}, P@5={avg_precision@5:.2f}, MRR={avg_MRR:.2f}"

    def __init__(self):
        super().__init__()
        self._test_set_path = os.path.join(self._plugin_dir(), "test_set.json")
        self._top_k = int(os.getenv("TOP_K", 5))
        self._rag_endpoint = os.getenv("RAG_ENDPOINT", "http://localhost:8000/retrieve")

    def _load_test_set(self) -> List[Dict[str, any]]:
        """Load the test set of queries and ground-truth relevant chunk IDs.

        If the file does not exist (e.g. on first run) a small default set of
        realistic RAG queries is created and persisted so subsequent ticks see
        the same stable test set.
        """
        test_set_path = self._test_set_path
        if not os.path.exists(test_set_path):
            default = [
                {
                    "query": "What is retrieval augmented generation?",
                    "relevant_chunk_ids": ["chunk_001", "chunk_002"],
                },
                {
                    "query": "How does RAG handle out-of-domain queries?",
                    "relevant_chunk_ids": ["chunk_003", "chunk_004"],
                },
                {
                    "query": "What are the key components of a RAG pipeline?",
                    "relevant_chunk_ids": ["chunk_005", "chunk_006"],
                },
                {
                    "query": "Explain chunking strategies for document retrieval",
                    "relevant_chunk_ids": ["chunk_007", "chunk_008"],
                },
                {
                    "query": "What is the role of embedding models in RAG?",
                    "relevant_chunk_ids": ["chunk_009", "chunk_010"],
                },
            ]
            print(
                f"info: {test_set_path} not found, creating default test set",
                file=sys.stderr,
            )
            os.makedirs(os.path.dirname(test_set_path), exist_ok=True)
            with open(test_set_path, "w", encoding="utf-8") as f:
                json.dump(default, f, separators=(",", ":"), sort_keys=True)
                f.write("\n")
            return default
        with open(test_set_path, "r", encoding="utf-8") as f:
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

        state = self._load_persisted_state({"queries_run": 0, "queries_with_zero_recall": 0})
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

        self._save_persisted_state(state)

        return {
            "avg_recall@5": avg_recall_at_5,
            "avg_precision@5": avg_precision_at_5,
            "avg_MRR": avg_mrr,
            "results": results,
        }
