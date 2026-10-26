"""Opt-in Groq/OpenAI-compatible or Gemini examiner; other dependencies stay MOCK."""

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from src.agent.contracts import AgentError, DependencyFailure, ErrorCode, WritingSubmission
from src.agent.gemini import GeminiExaminer, load_gemini_settings
from src.agent.graph import build_graph
from src.agent.mock_services import make_mock_dependencies
from src.agent.openai_compatible import OpenAICompatibleExaminer, load_openai_settings
from src.agent.prompts import PROMPT_VERSION
from src.agent.tracing import write_jsonl

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("openai", "gemini"), default="openai")
    parser.add_argument("--task", choices=("task1", "task2"), default="task2")
    parser.add_argument("--submission", type=Path, help="Optional self-authored submission JSON")
    parser.add_argument(
        "--check-config", action="store_true", help="Validate config without API calls"
    )
    args = parser.parse_args(argv)
    try:
        settings = (
            load_openai_settings(ROOT / ".env")
            if args.provider == "openai"
            else load_gemini_settings(ROOT / ".env")
        )
    except DependencyFailure as exc:
        error = AgentError(
            run_id=str(uuid4()),
            code=exc.code,
            retry_count=0,
            errors=[],
            diagnostics=exc.diagnostics,
        )
        print(error.model_dump_json())
        print(
            "Configure provider API key/model/base URL in .env; see docs/live_llm.md.",
            file=sys.stderr,
        )
        return 2
    if args.check_config:
        print(json.dumps({"status": "configured", "model": settings.model, "api_called": False}))
        return 0
    target = args.submission or ROOT / "examples" / "fixtures" / f"live_{args.task}.json"
    try:
        submission = WritingSubmission.model_validate_json(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(
            AgentError(
                run_id=str(uuid4()), code=ErrorCode.INVALID_INPUT, retry_count=0, errors=[]
            ).model_dump_json()
        )
        return 2
    examiner = None
    try:
        examiner = (
            OpenAICompatibleExaminer(settings)
            if args.provider == "openai"
            else GeminiExaminer(settings)
        )
        deps = replace(
            make_mock_dependencies(),
            examiner=examiner,
            model_version=getattr(settings, "trace_model_version", settings.model),
            prompt_version=PROMPT_VERSION,
        )
        output = build_graph(dependencies=deps).invoke(
            {"request": submission.model_dump(mode="json")}
        )
        result = output["result"]
        calls = [e for e in output["trace"] if e.node == "examiner_generate"]
        print(
            json.dumps(
                {
                    "mode": f"REAL_{args.provider.upper()}_WITH_MOCK_BANK_RAG_TOOLS_VALIDATORS",
                    "model": settings.model,
                    "result": result.model_dump(mode="json"),
                    "generation_attempts": len(calls),
                    "usage_per_attempt": [
                        {
                            "attempt": e.attempt,
                            "input_tokens": e.input_tokens,
                            "output_tokens": e.output_tokens,
                        }
                        for e in calls
                    ],
                    "provider_diagnostics": [
                        {
                            "attempt": event.attempt,
                            **event.provider_diagnostics.model_dump(mode="json"),
                        }
                        for event in calls
                        if event.provider_diagnostics is not None
                    ],
                    "estimated_cost_usd": None,
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        directory = ROOT / "artifacts" / "traces"
        directory.mkdir(parents=True, exist_ok=True)
        write_jsonl(directory / f"live_{result.run_id}.jsonl", output["trace"])
        return 0 if result.status == "success" else 1
    except DependencyFailure as exc:
        print(
            AgentError(
                run_id=str(uuid4()),
                code=exc.code,
                retry_count=0,
                errors=[],
                diagnostics=exc.diagnostics,
            ).model_dump_json()
        )
        return 2
    finally:
        if examiner is not None:
            examiner.close()


if __name__ == "__main__":
    raise SystemExit(main())
