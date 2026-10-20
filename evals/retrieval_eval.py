"""Measure ranking against authored relevance IDs, separately from grading evals."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.descriptor_data import ROOT, CRITERIA
from src.tools.rag_descriptors import DescriptorRetriever, RetrievalError, QUERY_VERSION, _arguments


def ranking_metrics(retrieved_ids, relevant_ids, k):
    if type(k) is not int or k < 1:
        raise ValueError("k must be positive")
    relevant = set(relevant_ids)
    if not relevant or len(retrieved_ids) != len(set(retrieved_ids)):
        raise ValueError("Require relevance labels and unique retrieved IDs")
    ranked = retrieved_ids[:k]
    hits = [rank for rank, cid in enumerate(ranked, 1) if cid in relevant]
    return {"precision_at_k": len(hits) / k, "recall_at_k": len(hits) / len(relevant),
            "reciprocal_rank": 1 / hits[0] if hits else 0.0}


def load_queries(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list) or not data["cases"]:
        raise ValueError("Require non-empty retrieval cases")
    seen = set()
    for case in data["cases"]:
        task, criterion = _arguments(case["task_type"], case["criterion"], 3)
        if not isinstance(case["case_id"], str) or case["case_id"] in seen:
            raise ValueError("Invalid/duplicate case ID")
        seen.add(case["case_id"])
        if not isinstance(case["query"], str) or not case["query"].strip():
            raise ValueError("Empty query")
        refs = case["relevant_ids"]
        permitted = {f"writing_{task}_{criterion}_b{b}_2023_05" for b in range(1, 10)}
        if not isinstance(refs, list) or not refs or any(not isinstance(r, str) for r in refs):
            raise ValueError("Require relevant IDs")
        if len(set(refs)) != len(refs) or not set(refs) <= permitted:
            raise ValueError("Invalid relevance labels")
    return data


def evaluate(retriever, dataset, *, top_k=3, mode="query"):
    if mode not in {"query", "criterion"}:
        raise ValueError("Unknown evaluation mode")
    results = []
    for case in dataset["cases"]:
        error = None
        try:
            if mode == "query":
                chunks = retriever.retrieve_for_query(case["task_type"], case["criterion"], case["query"], top_k)
            else:
                chunks = retriever.retrieve_descriptors(case["task_type"], case["criterion"], top_k)
            ids = [c.chunk_id for c in chunks]
        except RetrievalError as exc:
            ids, error = [], {"code": exc.code, "reason": exc.reason}
        results.append({"case_id": case["case_id"], "retrieved_ids": ids,
                        "relevant_ids": case["relevant_ids"], "error": error,
                        **ranking_metrics(ids, case["relevant_ids"], top_k)})
    count = len(results)
    if count == 0:
        raise ValueError("Cannot evaluate an empty dataset")
    means = {name: sum(r[name] for r in results) / count
             for name in ("precision_at_k", "recall_at_k", "reciprocal_rank")}
    means["mrr_at_k"] = means.pop("reciprocal_rank")
    return {"mode": mode, "top_k": top_k, "case_count": count,
            "error_count": sum(r["error"] is not None for r in results),
            "metrics": means, "cases": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, default=ROOT / "evals/data/retrieval_queries.json")
    parser.add_argument("--db-path", type=Path, default=ROOT / "data/chroma_db")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/member2/retrieval_results.json")
    parser.add_argument("--top-k", type=int, choices=(1, 2, 3), default=3)
    parser.add_argument("--mode", choices=("query", "criterion", "both"), default="both")
    args = parser.parse_args()
    dataset = load_queries(args.queries)
    retriever = DescriptorRetriever(args.db_path)
    # Do not publish an all-zero metric report when no actual index was available.
    try:
        collection = retriever._open_collection()
    except RetrievalError as exc:
        parser.exit(1, f"Evaluation unavailable: {exc}. Build the Member 1 index first.\n")
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "query_version": QUERY_VERSION,
        "dataset_sha256": hashlib.sha256(args.queries.read_bytes()).hexdigest(),
        "dataset_metadata": dataset.get("metadata", {}),
        "index_metadata": collection.metadata,
        "scope": "Retrieval ranking only; not benchmark grading accuracy or injection robustness.",
        "runs": [evaluate(retriever, dataset, top_k=args.top_k, mode=mode)
                 for mode in (("query", "criterion") if args.mode == "both" else (args.mode,))],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "runs": [
        {k: run[k] for k in ("mode", "top_k", "case_count", "error_count", "metrics")}
        for run in report["runs"]]}, indent=2))
    if any(run["error_count"] for run in report["runs"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
