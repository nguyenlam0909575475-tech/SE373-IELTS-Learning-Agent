"""Regenerate synthetic handoff examples from the public SSOT and actual graph."""

import json
from pathlib import Path

from src.agent.graph import build_graph
from src.agent.mock_services import make_mock_dependencies
from src.agent.schemas import Criterion, TaskType


def main() -> None:
    deps = make_mock_dependencies()
    request = {"item_id": "MOCK_T2_001", "task_type": "task2", "essay": "Synthetic library essay."}
    result = build_graph(dependencies=deps).invoke({"request": request})["result"]
    failure = build_graph(dependencies=make_mock_dependencies(failures_before_success=99))
    error = failure.invoke({"request": request})["result"]
    example = {
        "label": "MOCK synthetic examples; not real IELTS grades",
        "submission_N5": request,
        "success_N3_to_N5": result.model_dump(mode="json"),
        "error_N3_to_N5": error.model_dump(mode="json"),
        "retrieval_N2_to_N3": [
            c.model_dump(mode="json")
            for c in deps.retriever.retrieve_descriptors(TaskType.TASK2, Criterion.TASK_RESPONSE)
        ],
        "plagiarism_N4_to_N3": deps.tools.check_plagiarism(request["essay"]).model_dump(
            mode="json"
        ),
        "security_N4_to_N3": {"injection_detected": False},
        "validator_N4_to_N3": [{"code": "evidence_invalid", "criterion": "task_response"}],
    }
    target = Path("docs/examples/contracts.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(example, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Generated MOCK contracts in docs/examples/contracts.json")


if __name__ == "__main__":
    main()
