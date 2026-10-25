"""Live Agent Connector for UC-02.

Invoked when USE_MOCK_AGENT is False. Integrates with the LangGraph StateGraph
and Examiner agent using OpenAI-compatible (Groq) or Gemini API.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path
from typing import Literal

from skills.writing_assessment.checks import WritingAssessment
from src.agent.contracts import ResolvedWritingTask
from src.agent.graph import build_graph
from src.agent.mock_services import make_mock_dependencies
from src.agent.openai_compatible import OpenAICompatibleExaminer, load_openai_settings

logger = logging.getLogger("backend.live_service")
ROOT_DIR = Path(__file__).resolve().parent.parent


def run_live_assessment(
    task_type: Literal["task1", "task2"],
    prompt: str,
    essay: str,
) -> WritingAssessment:
    """Execute live assessment pipeline via LLM and LangGraph StateGraph."""
    try:
        settings = load_openai_settings(ROOT_DIR / ".env")
        examiner = OpenAICompatibleExaminer(settings)
    except Exception as err:
        logger.error("Failed to initialize live LLM examiner: %s", err)
        raise RuntimeError(
            f"Failed to initialize LLM provider. Check .env configuration: {err}"
        ) from err

    item_id = f"LIVE_{task_type.upper()}_001"

    class DynamicTaskBank:
        def resolve(self, requested_id: str) -> ResolvedWritingTask:
            return ResolvedWritingTask(
                item_id=requested_id,
                task_type=task_type,
                task_prompt=prompt or "Evaluate this IELTS essay according to band descriptors.",
                source="self_written",
                license="CC0-1.0",
            )

    deps = replace(
        make_mock_dependencies(),
        task_bank=DynamicTaskBank(),
        examiner=examiner,
        model_version=getattr(settings, "trace_model_version", settings.model),
    )

    graph = build_graph(dependencies=deps)
    output = graph.invoke(
        {
            "request": {
                "item_id": item_id,
                "task_type": task_type,
                "essay": essay,
            }
        }
    )

    result = output["result"]
    if result.status != "success":
        error_msg = f"Live assessment failed with code: {result.code} (retry_count={result.retry_count})"
        if getattr(result, "diagnostics", None):
            diag = result.diagnostics
            if diag.http_status == 429:
                error_msg += f". Rate limit exceeded, please retry after {diag.retry_after_seconds}s."
            else:
                error_msg += f" [HTTP {diag.http_status}]"
        raise RuntimeError(error_msg)

    data = result.assessment.model_dump(mode="json")
    for crit in data["criteria"]:
        if crit["criterion"] == "coherence_cohesion":
            crit["criterion"] = "coherence_and_cohesion"
        elif crit["criterion"] == "grammatical_range_accuracy":
            crit["criterion"] = "grammatical_range_and_accuracy"

    return WritingAssessment.model_validate(data)
