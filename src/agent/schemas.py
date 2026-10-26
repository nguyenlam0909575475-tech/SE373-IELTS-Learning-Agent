"""Public UC-02 assessment SSOT; team choices are documented in docs/contracts.md."""

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StringConstraints,
    model_validator,
)

DISCLAIMER = "Điểm ước lượng do AI chấm, chỉ dùng để luyện tập, không thay thế điểm thi chính thức"


def nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("blank string")
    return value  # Preserve Unicode/whitespace for exact offsets.


Text = Annotated[str, StringConstraints(strict=True, min_length=1), AfterValidator(nonblank)]
Band = Annotated[float, Field(strict=True, ge=0, le=9, allow_inf_nan=False)]


class PublicModel(BaseModel):
    model_config = ConfigDict(extra="forbid", revalidate_instances="always")


class TaskType(StrEnum):
    TASK1 = "task1"
    TASK2 = "task2"


class Criterion(StrEnum):
    TASK_ACHIEVEMENT = "task_achievement"
    TASK_RESPONSE = "task_response"
    COHERENCE_COHESION = "coherence_cohesion"
    LEXICAL_RESOURCE = "lexical_resource"
    GRAMMATICAL_RANGE_ACCURACY = "grammatical_range_accuracy"


def criteria_for(task_type: TaskType) -> tuple[Criterion, ...]:
    first = Criterion.TASK_ACHIEVEMENT if task_type == TaskType.TASK1 else Criterion.TASK_RESPONSE
    return (
        first,
        Criterion.COHERENCE_COHESION,
        Criterion.LEXICAL_RESOURCE,
        Criterion.GRAMMATICAL_RANGE_ACCURACY,
    )


class Flag(StrEnum):
    UNDER_LENGTH = "under_length"
    OFF_TOPIC = "off_topic"
    POSSIBLE_PLAGIARISM = "possible_plagiarism"
    INJECTION_DETECTED = "injection_detected"


class CorrectionCategory(StrEnum):
    GRAMMAR = "grammar"
    LEXIS = "lexis"
    COHESION = "cohesion"
    TASK = "task"


class Evidence(PublicModel):
    quote: Text
    start_char: Annotated[StrictInt, Field(ge=0)]
    end_char: Annotated[StrictInt, Field(gt=0)]

    @model_validator(mode="after")
    def ordered_span(self) -> Self:
        if self.end_char <= self.start_char:
            raise ValueError("end_char must exceed start_char")
        return self


class CriterionAssessment(PublicModel):
    criterion: Criterion
    band: Band
    evidence: Annotated[list[Evidence], Field(min_length=1)]
    descriptor_refs: Annotated[list[Text], Field(min_length=1)]
    comment: Text


class Correction(PublicModel):
    original: Text
    suggestion: Text
    reason: Text
    category: CorrectionCategory


class PriorityLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImprovementPriority(PublicModel):
    """Ranked improvement action: tells the student what to fix first and why."""

    rank: Annotated[int, Field(strict=True, ge=1, le=5)]
    title: Text
    example_quote: Text
    why_it_matters: Text
    fix_principle: Text
    related_criterion: Criterion


class ErrorPattern(PublicModel):
    """Recurring error pattern with frequency count and grouped instances."""

    pattern_name: Text
    category: CorrectionCategory
    frequency: Annotated[int, Field(strict=True, ge=1)]
    priority: PriorityLevel
    rule: Text
    instances: list[Correction]


class SentenceRewrite(PublicModel):
    """Minimal sentence-level edit that preserves the student's original ideas."""

    original_sentence: Text
    rewritten_sentence: Text
    changes_made: list[Text]


class ParagraphAnalysis(PublicModel):
    """Per-paragraph feedback on structure and content."""

    paragraph_number: Annotated[int, Field(strict=True, ge=1)]
    paragraph_role: Text
    what_works: Text
    what_to_improve: Text


class GrammarRule(PublicModel):
    """High-impact grammar or vocabulary rule derived from the student's recurring errors."""

    rule_name: Text
    explanation: Text
    incorrect_example: Text
    correct_example: Text


class ModelSentence(PublicModel):
    """Reusable model sentence with highlighted useful phrases."""

    sentence: Text
    useful_phrases: list[Text]


class WritingAssessment(PublicModel):
    task_type: TaskType
    word_count: Annotated[StrictInt, Field(ge=0)]
    criteria: Annotated[list[CriterionAssessment], Field(min_length=4, max_length=4)]
    overall_band: Band
    corrections: list[Correction]
    flags: list[Flag]
    disclaimer: Text
    # --- Pedagogical feedback (optional, populated by live LLM examiner) ---
    top_priorities: list[ImprovementPriority] = []
    error_patterns: list[ErrorPattern] = []
    sentence_rewrites: list[SentenceRewrite] = []
    paragraph_analyses: list[ParagraphAnalysis] = []
    grammar_rules: list[GrammarRule] = []
    model_sentences: list[ModelSentence] = []

    @model_validator(mode="after")
    def task_criteria_and_disclaimer(self) -> Self:
        if {c.criterion for c in self.criteria} != set(criteria_for(self.task_type)):
            raise ValueError("four distinct criteria must match task_type")
        if self.disclaimer != DISCLAIMER:
            raise ValueError("required estimate disclaimer")
        if len(set(self.flags)) != len(self.flags):
            raise ValueError("duplicate flags")
        return self
