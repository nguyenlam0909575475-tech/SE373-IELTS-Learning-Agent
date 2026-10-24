import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from evals.retrieval_eval import evaluate, load_queries, ranking_metrics
from src.tools.rag_descriptors import RetrievalError

ROOT = Path(__file__).resolve().parents[1]


class RetrievalEvalTests(unittest.TestCase):
    def test_hand_calculated_metrics(self):
        metrics = ranking_metrics(["irrelevant", "b", "a"], ["a", "b", "c", "d"], 3)
        self.assertEqual(metrics, {"precision_at_k": 2 / 3, "recall_at_k": 0.5, "reciprocal_rank": 0.5})

    def test_missing_results_count_as_precision_misses(self):
        self.assertEqual(ranking_metrics(["a"], ["a", "b"], 3),
                         {"precision_at_k": 1 / 3, "recall_at_k": 0.5, "reciprocal_rank": 1.0})
        self.assertEqual(ranking_metrics([], ["a"], 3)["reciprocal_rank"], 0)

    def test_duplicate_ids_or_empty_labels_are_invalid(self):
        for ids, gold in [(["a", "a"], ["a"]), (["a"], [])]:
            with self.assertRaises(ValueError):
                ranking_metrics(ids, gold, 3)

    def test_dataset_has_eight_scopes_and_unique_cases(self):
        data = load_queries(ROOT / "evals/data/retrieval_queries.json")
        self.assertEqual(len(data["cases"]), 16)
        self.assertEqual(len({(c["task_type"], c["criterion"]) for c in data["cases"]}), 8)

    def test_wrong_scope_label_is_rejected(self):
        data = load_queries(ROOT / "evals/data/retrieval_queries.json")
        data["cases"][0]["relevant_ids"] = ["writing_task2_task_response_b5_2023_05"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queries.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_queries(path)

    def test_failed_queries_stay_in_macro_average(self):
        dataset = {"cases": [dict(case_id="a", task_type="task2", criterion="lexical_resource", query="q", relevant_ids=["hit"]),
                             dict(case_id="b", task_type="task2", criterion="lexical_resource", query="r", relevant_ids=["hit"])]}
        retriever = Mock()
        retriever.retrieve_for_query.side_effect = [[SimpleNamespace(chunk_id="hit")], RetrievalError("query_failed")]
        result = evaluate(retriever, dataset, top_k=1)
        self.assertEqual(result["error_count"], 1)
        self.assertEqual(result["metrics"]["precision_at_k"], 0.5)
        self.assertEqual(result["metrics"]["mrr_at_k"], 0.5)

    def test_criterion_mode_uses_production_entrypoint(self):
        data = load_queries(ROOT / "evals/data/retrieval_queries.json")
        data["cases"] = data["cases"][:1]
        retriever = Mock()
        retriever.retrieve_descriptors.return_value = [SimpleNamespace(chunk_id=data["cases"][0]["relevant_ids"][0])]
        report = evaluate(retriever, data, mode="criterion")
        self.assertEqual(report["metrics"]["recall_at_k"], 1)
        retriever.retrieve_for_query.assert_not_called()


if __name__ == "__main__":
    unittest.main()
