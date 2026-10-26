"""Live UC-02 composition using real N2 retrieval and N4 corpus/tools/checks."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from skills.writing_assessment.checks import WritingAssessment
from src.agent.contracts import DependencyFailure, ErrorCode, ResolvedWritingTask
from src.agent.graph import build_graph
from src.agent.openai_compatible import OpenAICompatibleExaminer, load_openai_settings
from src.agent.team_adapters import MappingTaskBank, build_team_dependencies
from src.tools.rag_descriptors import DescriptorRetriever

ROOT_DIR = Path(__file__).resolve().parent.parent


class LiveAssessmentError(RuntimeError):
    """Stable metadata without provider messages or submission contents."""

    def __init__(self, code, *, retry_count=0, errors=(), diagnostics=None):
        self.code = ErrorCode(code)
        self.retry_count = retry_count
        self.errors = [item.model_dump(mode="json") for item in errors]
        self.diagnostics = diagnostics.model_dump(mode="json") if diagnostics is not None else None
        super().__init__(self.code.value)


@lru_cache(maxsize=1)
def get_live_retriever():
    """Reuse N2's lazily opened collection; never rebuild the DB in a request."""
    from src.agent.contracts import DescriptorChunk

    return DescriptorRetriever(chunk_factory=lambda **row: DescriptorChunk.model_validate(row))


def run_live_assessment(
    task_type: Literal["task1", "task2"],
    prompt: str,
    essay: str,
    *,
    task_material_text: str | None = None,
    source_url: str | None = None,
) -> WritingAssessment:
    """Run the team graph. Task 1 needs actual chart/table data transcribed as text."""
    if not prompt.strip():
        raise LiveAssessmentError(ErrorCode.INVALID_TASK)
    if task_type == "task1" and not (task_material_text and task_material_text.strip()):
        raise LiveAssessmentError(ErrorCode.INVALID_TASK)

    examiner = None
    try:
        settings = load_openai_settings(ROOT_DIR / ".env")
        examiner = OpenAICompatibleExaminer(settings)
        item_id = f"LIVE_{task_type.upper()}_001"
        task = ResolvedWritingTask(
            item_id=item_id,
            task_type=task_type,
            task_prompt=prompt,
            task_material_text=task_material_text,
            source="public" if source_url else "user_provided",
            source_url=source_url,
        )
        deps = build_team_dependencies(
            task_bank=MappingTaskBank({item_id: task}),
            examiner=examiner,
            retriever=get_live_retriever(),
            model_version=settings.trace_model_version,
        )
        output = build_graph(dependencies=deps).invoke(
            {"request": {"item_id": item_id, "task_type": task_type, "essay": essay}}
        )
        result = output["result"]
        if result.status != "success":
            raise LiveAssessmentError(
                result.code, retry_count=result.retry_count,
                errors=result.errors, diagnostics=result.diagnostics,
            )

        # N5's existing API uses legacy criterion spellings. The graph keeps
        # canonical names and exact code-point offsets on the original essay.
        data = result.assessment.model_dump(mode="json")
        aliases = {"coherence_cohesion": "coherence_and_cohesion",
                   "grammatical_range_accuracy": "grammatical_range_and_accuracy"}
        for criterion in data["criteria"]:
            criterion["criterion"] = aliases.get(criterion["criterion"], criterion["criterion"])
        return WritingAssessment.model_validate(data)
    except DependencyFailure as exc:
        raise LiveAssessmentError(exc.code, diagnostics=exc.diagnostics) from None
    finally:
        if examiner is not None:
            examiner.close()
