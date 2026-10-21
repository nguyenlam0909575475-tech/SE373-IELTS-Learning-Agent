"""Deterministic verification checks for the writing-assessment skill (UC-02 & UC-07).

This module belongs to the Harness verification layer. It validates:
1. Schema compliance of `WritingAssessment` (Pydantic v2).
2. Valid IELTS band increments [1.0, 1.5, ..., 9.0] and the repository Task-band rounding policy.
3. Exact 4 IELTS criteria matching `task1` (`task_achievement`) or `task2` (`task_response`).
4. 100% verbatim existence of `evidence.quote` in `essay_text` and exact `[start_char:end_char]` slice matching.
5. 100% validity of `descriptor_refs` against retrieved RAG chunk IDs and `task_type` (`task1` vs `task2`).
6. Mandatory penalty rules (`under_length` flag when <150/<250 words; `off_topic` caps TR/TA at <= 5.0).
7. Presence of the mandatory AI estimation disclaimer (Rule 1.5.2).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from agent.tools.compute_tool import compute_band

from .validators import consistency_validator, format_issue, quote_validator, refs_validator

VALID_BANDS: set[float] = {i / 2.0 for i in range(2, 19)}  # {1.0, 1.5, ..., 9.0}

DEFAULT_DISCLAIMER = (
    "Điểm ước lượng do AI chấm, chỉ dùng để luyện tập, không thay thế điểm thi chính thức."
)

CriterionName = Literal[
    "task_achievement",
    "task_response",
    "coherence_and_cohesion",
    "lexical_resource",
    "grammatical_range_and_accuracy",
]

FlagType = Literal[
    "under_length",
    "off_topic",
    "possible_plagiarism",
    "injection_detected",
]

CorrectionCategory = Literal["grammar", "lexis", "cohesion", "task"]


class EvidenceSpan(BaseModel):
    quote: str = Field(
        ..., min_length=1, description="Verbatim substring from the student's essay."
    )
    start_char: int = Field(
        ..., ge=0, description="0-indexed start character offset in essay_text."
    )
    end_char: int = Field(..., gt=0, description="0-indexed end character offset in essay_text.")


class CriterionAssessment(BaseModel):
    criterion: CriterionName
    band: float
    evidence: list[EvidenceSpan] = Field(..., min_length=1)
    descriptor_refs: list[str] = Field(..., min_length=1)
    comment: str = Field(..., min_length=1)


class CorrectionItem(BaseModel):
    original: str = Field(..., min_length=1)
    suggestion: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    category: CorrectionCategory


class WritingAssessment(BaseModel):
    task_type: Literal["task1", "task2"]
    word_count: int = Field(..., ge=1)
    criteria: list[CriterionAssessment] = Field(..., min_length=4, max_length=4)
    overall_band: float
    corrections: list[CorrectionItem] = Field(default_factory=list)
    flags: list[FlagType] = Field(default_factory=list)
    disclaimer: str = Field(default=DEFAULT_DISCLAIMER, min_length=10)


class ValidationResult(BaseModel):
    passed: bool
    errors: list[str] = Field(default_factory=list)
    assessment: WritingAssessment | None = None


def compute_ielts_overall_band(bands: Sequence[float]) -> float:
    """Compatibility name retained for N3; N4 owns the shared calculation."""
    return compute_band(bands)


def repair_evidence_offsets(raw_data: dict[str, Any], essay_text: str) -> dict[str, Any]:
    """Locate exact start_char and end_char in essay_text if quote exists verbatim."""
    criteria = raw_data.get("criteria")
    if not isinstance(criteria, list):
        return raw_data

    for crit in criteria:
        if not isinstance(crit, dict):
            continue
        evidences = crit.get("evidence")
        if not isinstance(evidences, list):
            continue
        for ev in evidences:
            if not isinstance(ev, dict):
                continue
            quote = ev.get("quote")
            if isinstance(quote, str) and quote:
                start = ev.get("start_char")
                end = ev.get("end_char")
                if (
                    not isinstance(start, int)
                    or not isinstance(end, int)
                    or essay_text[start:end] != quote
                ):
                    idx = essay_text.find(quote)
                    if idx != -1:
                        ev["start_char"] = idx
                        ev["end_char"] = idx + len(quote)
    return raw_data


def validate_writing_assessment(
    raw_output: dict[str, Any] | WritingAssessment,
    essay_text: str,
    expected_task_type: Literal["task1", "task2"] | None = None,
    expected_word_count: int | None = None,
    retrieved_descriptor_ids: set[str] | list[str] | None = None,
    *,
    retrieved_descriptors: list | None = None,
    plagiarism_result: object | None = None,
    security_result: object | None = None,
    off_topic: bool | None = None,
) -> ValidationResult:
    """Validate N3 output using shared N4 tools.

    Supply count_words(essay_text) as expected_word_count. Full descriptor
    chunks enable metadata checks; the legacy IDs-only argument still works.
    Trusted plagiarism/security/off-topic signals are checked only if supplied.
    The caller must handle missing tools and retry or stop before displaying.
    """
    errors: list[str] = []

    if isinstance(raw_output, WritingAssessment):
        assessment = raw_output
    else:
        try:
            assessment = WritingAssessment.model_validate(raw_output)
        except ValidationError as exc:
            for err in exc.errors():
                loc = ".".join(str(p) for p in err["loc"])
                errors.append(f"Schema error at '{loc}': {err['msg']}")
            return ValidationResult(passed=False, errors=errors, assessment=None)

    # 1. Task type consistency
    if expected_task_type and assessment.task_type != expected_task_type:
        errors.append(
            f"task_type mismatch: expected '{expected_task_type}', got '{assessment.task_type}'."
        )

    # 2. Word count consistency (must come from deterministic tool, not LLM guess)
    if expected_word_count is not None and assessment.word_count != expected_word_count:
        errors.append(
            f"word_count mismatch: tool counted {expected_word_count}, output has {assessment.word_count}."
        )

    # 3. Required 4 criteria names per task_type
    first_criterion = "task_achievement" if assessment.task_type == "task1" else "task_response"
    expected_criteria = {
        first_criterion,
        "coherence_and_cohesion",
        "lexical_resource",
        "grammatical_range_and_accuracy",
    }
    actual_criteria = [c.criterion for c in assessment.criteria]
    if set(actual_criteria) != expected_criteria:
        errors.append(
            f"Invalid criteria set for {assessment.task_type}: expected {sorted(expected_criteria)}, "
            f"got {sorted(actual_criteria)}."
        )

    # 4. Band step validation & overall_band calculation check
    criterion_bands: list[float] = []
    task_criterion_band: float | None = None

    for crit in assessment.criteria:
        if crit.band not in VALID_BANDS:
            errors.append(
                f"Invalid band {crit.band} for '{crit.criterion}'. Must be in [1.0, 1.5, ..., 9.0]."
            )
        criterion_bands.append(crit.band)
        if crit.criterion in ("task_achievement", "task_response"):
            task_criterion_band = crit.band

    if assessment.overall_band not in VALID_BANDS:
        errors.append(
            f"Invalid overall_band {assessment.overall_band}. Must be in [1.0, 1.5, ..., 9.0]."
        )
    elif len(criterion_bands) == 4 and all(band in VALID_BANDS for band in criterion_bands):
        expected_overall = compute_ielts_overall_band(criterion_bands)
        if abs(assessment.overall_band - expected_overall) > 1e-6:
            errors.append(
                f"overall_band mismatch: expected {expected_overall} from criteria {criterion_bands}, "
                f"got {assessment.overall_band}."
            )

    # 5. Verbatim quote & character offset check + Descriptor reference check
    allowed_refs = set(retrieved_descriptor_ids) if retrieved_descriptor_ids is not None else None
    forbidden_prefix = "task1" if assessment.task_type == "task2" else "task2"

    errors.extend(format_issue(issue) for issue in quote_validator(assessment, essay_text))
    if retrieved_descriptors is not None:
        errors.extend(format_issue(issue) for issue in refs_validator(assessment, retrieved_descriptors))

    for crit in assessment.criteria:
        for ref in crit.descriptor_refs:
            if forbidden_prefix in ref.lower():
                errors.append(f"Criterion '{crit.criterion}' cites a descriptor for {forbidden_prefix}.")
            if allowed_refs is not None and ref not in allowed_refs:
                errors.append(f"Criterion '{crit.criterion}' cites an unretrieved descriptor_ref.")

    # 6. Under-length flag check (<150 words for Task 1, <250 words for Task 2)
    min_words = 150 if assessment.task_type == "task1" else 250
    if assessment.word_count < min_words and "under_length" not in assessment.flags:
        errors.append(
            f"Essay has {assessment.word_count} words (< {min_words} for {assessment.task_type}), "
            f"but 'under_length' is missing from flags."
        )

    # 7. Off-topic penalty check (UC-02 Acceptance Criterion #4: off_topic must have TR/TA <= 5.0)
    if (
        "off_topic" in assessment.flags
        and task_criterion_band is not None
        and task_criterion_band > 5.0
    ):
        errors.append(
            f"Essay is flagged 'off_topic', so {first_criterion} band must be <= 5.0 "
            f"(got {task_criterion_band})."
        )

    # N4 consistency includes supplied trusted sensor signals; None is unknown.
    errors.extend(format_issue(issue) for issue in consistency_validator(
        assessment,
        word_count=expected_word_count if expected_word_count is not None else assessment.word_count,
        plagiarism=plagiarism_result,
        security=security_result,
        off_topic=off_topic,
    ))

    # 8. Mandatory AI estimation disclaimer check (Rule 1.5.2)
    disclaimer_lower = assessment.disclaimer.lower()
    if "ước lượng" not in disclaimer_lower and "estimate" not in disclaimer_lower:
        errors.append(
            "Missing mandatory AI score estimation disclaimer in 'disclaimer' field (Rule 1.5.2)."
        )

    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        assessment=assessment if len(errors) == 0 else None,
    )
