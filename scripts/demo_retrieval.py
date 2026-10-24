"""Run all eight retrieval scopes and save a metadata-only sample trace."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from scripts.descriptor_data import CRITERIA, ROOT
from src.tools.rag_descriptors import QUERY_VERSION, DescriptorRetriever, RetrievalError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=ROOT / "data/chroma_db")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/member2/retrieval_trace.json")
    args = parser.parse_args()
    retriever = DescriptorRetriever(args.db_path)
    trace = {"run_id": str(uuid4()), "created_at": datetime.now(timezone.utc).isoformat(),
             "scope": "Member 2 retrieval demo only; no examiner or learner data.",
             "query_version": QUERY_VERSION, "calls": []}
    for task, criteria in CRITERIA.items():
        for criterion in criteria:
            started = perf_counter()
            call = {"tool": "retrieve_descriptors", "parameters": {
                "task_type": task, "criterion": criterion, "top_k": 3}}
            try:
                chunks = retriever.retrieve_descriptors(task, criterion)
                call["status"] = "success"
                call["result"] = [{k: getattr(c, k) for k in ("chunk_id", "test_part", "criterion", "band", "version")} for c in chunks]
            except RetrievalError as exc:
                call.update(status="error", error={"code": exc.code, "reason": exc.reason})
            call["elapsed_ms"] = round((perf_counter() - started) * 1000, 3)
            trace["calls"].append(call)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    errors = sum(call["status"] == "error" for call in trace["calls"])
    print(json.dumps({"run_id": trace["run_id"], "calls": len(trace["calls"]), "errors": errors, "trace": str(args.output)}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
