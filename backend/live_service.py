"""Live Agent Connector for UC-02 (Member 3 LangGraph StateGraph).

Invoked by the backend to execute the IELTS Writing assessment pipeline.
Supports:
- OpenAI-compatible LLM (Groq / OpenAI) via OPENAI_API_KEY
- Google Gemini LLM via GEMINI_API_KEY
- Deterministic fallback for offline testing and local CI when no API key is set.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Literal

from skills.writing_assessment.checks import WritingAssessment
from src.agent.contracts import (
    ResolvedWritingTask,
)
from src.agent.gemini import GeminiExaminer, load_gemini_settings
from src.agent.graph import build_graph
from src.agent.openai_compatible import OpenAICompatibleExaminer, load_openai_settings
from src.agent.schemas import (
    TaskType,
)
from src.agent.team_adapters import build_team_dependencies

logger = logging.getLogger("backend.live_service")
ROOT_DIR = Path(__file__).resolve().parent.parent





def _ensure_vectorstore() -> None:
    """Ensure ChromaDB exists before running live assessment."""
    db_path = ROOT_DIR / "data" / "chroma_db"
    if not (db_path / "chroma.sqlite3").is_file():
        logger.info("ChromaDB vectorstore not found; auto-building from processed descriptors...")
        from scripts.rebuild_vectorstore import rebuild
        source = ROOT_DIR / "data" / "processed" / "writing_descriptors.json"
        rebuild(source, db_path)


def _get_examiner() -> tuple[Any, str]:
    """Obtain live LLM examiner configured in .env (OpenAI-compatible or Gemini).
    
    100% reliant on Member 3 Agent Core with real LLM.
    Raises RuntimeError if neither provider is configured.
    """
    from dotenv import dotenv_values
    env_path = ROOT_DIR / ".env"
    env_vals = dotenv_values(env_path, interpolate=False) if env_path.is_file() else {}

    # Purge stale keys from os.environ if they were removed from .env
    for stale_key in ("OPENAI_API_KEY", "GEMINI_API_KEY", "OPENAI_MODEL", "GEMINI_MODEL"):
        if stale_key not in env_vals and stale_key in os.environ:
            os.environ.pop(stale_key, None)
    for k, v in env_vals.items():
        if v is not None:
            os.environ[k] = v

    errors: list[str] = []

    has_gemini = bool(env_vals.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY"))
    has_openai = bool(env_vals.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY"))

    def try_gemini():
        try:
            gemini_settings = load_gemini_settings(env_path)
            logger.info("Using Gemini live examiner (%s)", gemini_settings.model)
            return GeminiExaminer(gemini_settings), gemini_settings.model
        except Exception as exc:
            errors.append(f"Gemini ({exc})")
            logger.warning("Gemini examiner initialization skipped: %s", exc)
            return None

    def try_openai():
        try:
            openai_settings = load_openai_settings(env_path)
            logger.info("Using OpenAI-compatible live examiner (%s)", openai_settings.model)
            return OpenAICompatibleExaminer(openai_settings), getattr(
                openai_settings, "trace_model_version", openai_settings.model
            )
        except Exception as exc:
            errors.append(f"OpenAI/Groq ({exc})")
            logger.warning("OpenAI examiner initialization skipped: %s", exc)
            return None

    # Determine priority based on configured keys
    if has_gemini and not has_openai:
        order = [try_gemini, try_openai]
    else:
        order = [try_openai, try_gemini]

    for attempt_fn in order:
        res = attempt_fn()
        if res is not None:
            return res

    detail = " | ".join(errors) if errors else "Chưa cấu hình API key"
    raise RuntimeError(
        f"Không tìm thấy cấu hình LLM hợp lệ trong .env. Chi tiết: {detail}. Vui lòng kiểm tra OPENAI_API_KEY hoặc GEMINI_API_KEY."
    )


def run_live_assessment(
    task_type: Literal["task1", "task2"],
    prompt: str,
    essay: str,
    use_mock: bool = False,
) -> WritingAssessment:
    """Execute assessment pipeline via Member 3 LangGraph StateGraph (100% Live Agent)."""
    _ensure_vectorstore()
    examiner, model_version = _get_examiner()
    item_id = f"LIVE_{task_type.upper()}_001"
    tt = TaskType.TASK1 if task_type == "task1" else TaskType.TASK2

    class DynamicTaskBank:
        def resolve(self, requested_id: str) -> ResolvedWritingTask:
            return ResolvedWritingTask(
                item_id=requested_id,
                task_type=tt,
                task_prompt=prompt or "Evaluate this IELTS essay according to band descriptors.",
                task_material_text=(
                    prompt if task_type == "task1" else None
                )
                or ("IELTS Task 1 visual material" if task_type == "task1" else None),
                source="self_written",
                license="CC0-1.0",
            )

    deps = build_team_dependencies(
        task_bank=DynamicTaskBank(),
        examiner=examiner,
        model_version=model_version,
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
            if getattr(diag, "http_status", None) == 429:
                error_msg += f". Rate limit exceeded, please retry after {diag.retry_after_seconds}s."
            elif getattr(diag, "http_status", None):
                error_msg += f" [HTTP {diag.http_status}]"
        raise RuntimeError(error_msg)

    data = result.assessment.model_dump(mode="json")
    for crit in data["criteria"]:
        if crit["criterion"] == "coherence_cohesion":
            crit["criterion"] = "coherence_and_cohesion"
        elif crit["criterion"] == "grammatical_range_accuracy":
            crit["criterion"] = "grammatical_range_and_accuracy"
        if "band" in crit:
            crit["band"] = float(round(float(crit["band"]) * 2) / 2)

    from agent.tools.compute_tool import compute_band as ielts_compute_band
    crit_bands = [crit["band"] for crit in data["criteria"]]
    data["overall_band"] = ielts_compute_band(crit_bands)

    return WritingAssessment.model_validate(data)


# Backward-compatible alias
run_agent_assessment = run_live_assessment
