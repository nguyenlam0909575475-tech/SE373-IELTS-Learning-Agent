"""Synthetic Task 1 and Task 2; no network, API keys, or grading accuracy claim."""

import json
from pathlib import Path

from src.agent.graph import build_graph
from src.agent.mock_services import make_mock_dependencies
from src.agent.tracing import write_jsonl


def main() -> None:
    graph = build_graph(dependencies=make_mock_dependencies())
    for task, count in (("task1", 150), ("task2", 250)):
        essay = " ".join(["Library"] * count)
        output = graph.invoke(
            {
                "request": {
                    "item_id": "MOCK_T1_001" if task == "task1" else "MOCK_T2_001",
                    "task_type": task,
                    "essay": essay,
                }
            }
        )
        print(json.dumps(output["result"].model_dump(mode="json"), ensure_ascii=True, indent=2))
        target = Path("artifacts/traces")
        target.mkdir(parents=True, exist_ok=True)
        write_jsonl(target / f"MOCK_{task}.jsonl", output["trace"])
        assert output["result"].status == "success"
    failure = build_graph(dependencies=make_mock_dependencies(failures_before_success=99))
    result = failure.invoke(
        {
            "request": {
                "item_id": "MOCK_T2_001",
                "task_type": "task2",
                "essay": "Synthetic failure fixture.",
            }
        }
    )["result"]
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=True, indent=2))
    assert result.status == "error" and result.retry_count == 2


if __name__ == "__main__":
    main()
