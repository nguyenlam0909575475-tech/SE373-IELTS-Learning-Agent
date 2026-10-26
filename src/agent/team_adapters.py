"""Adapters for the team's N2/N4 implementations."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from math import isclose
from typing import Any

from pydantic import TypeAdapter

from .contracts import (
    Dependencies,
    DependencyFailure,
    DescriptorChunk,
    ErrorCode,
    IssueCode,
    PlagiarismResult,
    ResolvedWritingTask,
    SecurityResult,
    ValidationIssue,
    WritingSubmission,
)
from .schemas import Criterion, TaskType, WritingAssessment

_LEGACY = {
    Criterion.COHERENCE_COHESION.value: "coherence_and_cohesion",
    Criterion.GRAMMATICAL_RANGE_ACCURACY.value: "grammatical_range_and_accuracy",
}
_CURRENT = {value: key for key, value in _LEGACY.items()}


def _plain(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if callable(getattr(value, "model_dump", None)):
        return value.model_dump(mode="python")
    return value


def _legacy_assessment(assessment: Any, *, overall_band: float | None = None) -> dict[str, Any]:
    payload = assessment.model_dump(mode="python")
    for item in payload["criteria"]:
        item["criterion"] = _LEGACY.get(item["criterion"], item["criterion"])
    if overall_band is not None:
        payload["overall_band"] = overall_band
    return payload


class MappingTaskBank:
    """TaskBank backed by trusted, validated records supplied by the host app."""
    def __init__(self, tasks: Mapping[str, ResolvedWritingTask | Mapping[str, Any]]):
        self._tasks = {
            item_id: ResolvedWritingTask.model_validate(task)
            for item_id, task in tasks.items()
        }
        if any(key != task.item_id for key, task in self._tasks.items()):
            raise ValueError("task bank key must match item_id")

    def resolve(self, item_id: str) -> ResolvedWritingTask | None:
        return self._tasks.get(item_id)


class TeamRetriever:
    def __init__(self, retriever: Any):
        self._retriever = retriever

    def retrieve_descriptors(
        self, task_type: TaskType, criterion: Criterion, top_k: int = 3
    ) -> list[DescriptorChunk]:
        try:
            rows = self._retriever.retrieve_descriptors(task_type, criterion, top_k)
            return TypeAdapter(list[DescriptorChunk]).validate_python(rows, strict=True)
        except Exception:
            raise DependencyFailure(ErrorCode.RETRIEVAL_INVALID) from None


class TeamTools:
    """Expose N4 word/plagiarism tools and retain the approved raw task mean."""
    def __init__(self, compute_module: Any, plagiarism_module: Any):
        self._compute = compute_module
        self._plagiarism = plagiarism_module

    def count_words(self, essay: str) -> int:
        try:
            return self._compute.count_words(essay)
        except Exception:
            raise DependencyFailure() from None

    def compute_band(self, bands: list[float]) -> float:
        if len(bands) != 4:
            raise DependencyFailure()
        try:
            return float(self._compute.compute_band(bands))
        except Exception:
            raise DependencyFailure() from None

    def check_plagiarism(self, essay: str) -> PlagiarismResult:
        try:
            return PlagiarismResult.model_validate(
                _plain(self._plagiarism.check_plagiarism(essay))
            )
        except Exception:
            # Missing licensed corpus is not a negative plagiarism result.
            raise DependencyFailure() from None

    def legacy_rounded_band(self, bands: list[float]) -> float:
        return self._compute.compute_band(bands)


class TeamSecurity:
    def __init__(self, guard: Any):
        self._guard = guard

    def inspect(
        self, submission: WritingSubmission, task: ResolvedWritingTask,
        chunks: list[DescriptorChunk],
    ) -> SecurityResult:
        try:
            return SecurityResult.model_validate(
                _plain(self._guard.inspect(submission=submission, task=task, chunks=chunks))
            )
        except Exception:
            raise DependencyFailure() from None


class TeamValidators:
    """Translate legacy criterion spellings and isolate N4's former band policy."""
    def __init__(self, validators: Any, tools: TeamTools):
        self._validators = validators
        self._tools = tools

    @staticmethod
    def _issues(rows: Any) -> list[ValidationIssue]:
        issues = []
        for row in rows:
            item = _plain(row)
            code = item.get("code")
            criterion = getattr(item.get("criterion"), "value", item.get("criterion"))
            if code not in {entry.value for entry in IssueCode}:
                raise DependencyFailure()
            criterion = _CURRENT.get(criterion, criterion)
            try:
                issues.append(ValidationIssue(
                    code=IssueCode(code),
                    criterion=Criterion(criterion) if criterion is not None else None,
                ))
            except (TypeError, ValueError):
                raise DependencyFailure() from None
        return issues

    def quote_validator(self, assessment: WritingAssessment, essay: str) -> list[ValidationIssue]:
        try:
            return self._issues(
                self._validators.quote_validator(_legacy_assessment(assessment), essay)
            )
        except DependencyFailure:
            raise
        except Exception:
            raise DependencyFailure() from None

    def refs_validator(
        self, assessment: WritingAssessment, chunks: list[DescriptorChunk]
    ) -> list[ValidationIssue]:
        try:
            legacy_chunks = []
            for chunk in chunks:
                row = chunk.model_dump(mode="python")
                row["criterion"] = _LEGACY.get(row["criterion"], row["criterion"])
                legacy_chunks.append(row)
            return self._issues(self._validators.refs_validator(
                _legacy_assessment(assessment), legacy_chunks
            ))
        except DependencyFailure:
            raise
        except Exception:
            raise DependencyFailure() from None

    def consistency_validator(
        self, assessment: WritingAssessment, *, word_count: int, overall_band: float,
        plagiarism: PlagiarismResult, security: SecurityResult, off_topic: bool,
    ) -> list[ValidationIssue]:
        try:
            raw_mean = sum(item.band for item in assessment.criteria) / 4
            if not isclose(assessment.overall_band, overall_band, rel_tol=0, abs_tol=1e-9):
                return [ValidationIssue(code=IssueCode.CONSISTENCY_ERROR)]
            if not isclose(overall_band, raw_mean, rel_tol=0, abs_tol=1e-9):
                return [ValidationIssue(code=IssueCode.CONSISTENCY_ERROR)]
            # N4's validator rechecks its half-band score policy. Supply a
            # private compatibility view while preserving the public raw mean.
            n4_band = self._tools.legacy_rounded_band(
                [item.band for item in assessment.criteria]
            )
            rows = self._validators.consistency_validator(
                _legacy_assessment(assessment, overall_band=n4_band),
                word_count=word_count,
                overall_band=n4_band,
                plagiarism=plagiarism,
                security=security,
                off_topic=off_topic,
            )
            return self._issues(rows)
        except DependencyFailure:
            raise
        except Exception:
            raise DependencyFailure() from None


def build_team_dependencies(
    *, task_bank: Any, examiner: Any, db_path: str | None = None,
    plagiarism_checker: Any | None = None, security_guard: Any | None = None,
    validators: Any | None = None, model_version: str = "team_model",
    prompt_version: str = "writing_assessment_1_0_0",
) -> Dependencies:
    """Compose teammate modules; the host app must provide a task bank and licensed corpus."""
    try:
        from agent.tools import compute_tool, plagiarism_tool, security_tool  # type: ignore[import-not-found, import-untyped]
        from skills.writing_assessment import validators as n4_validators  # type: ignore[import-not-found]
        from src.tools.rag_descriptors import DescriptorRetriever  # type: ignore[import-not-found]

        retriever = DescriptorRetriever(
            db_path=db_path,
            chunk_factory=lambda **row: DescriptorChunk.model_validate(row),
        )
        tools = TeamTools(compute_tool, plagiarism_checker or plagiarism_tool)
        return Dependencies(
            task_bank=task_bank,
            retriever=TeamRetriever(retriever),
            tools=tools,
            examiner=examiner,
            validators=TeamValidators(validators or n4_validators, tools),
            security=TeamSecurity(security_guard or security_tool.SecurityGuard()),
            model_version=model_version,
            prompt_version=prompt_version,
        )
    except DependencyFailure:
        raise
    except Exception:
        raise DependencyFailure() from None
