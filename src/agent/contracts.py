"""Team-proposed integration DTOs and synchronous dependency protocols (no production tools)."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Literal, Protocol, Self, runtime_checkable

from pydantic import Field, StrictBool, model_validator

from .schemas import (
    Band,
    Correction,
    Criterion,
    CriterionAssessment,
    ErrorPattern,
    Evidence,
    GrammarRule,
    ImprovementPriority,
    ModelSentence,
    ParagraphAnalysis,
    PublicModel,
    SentenceRewrite,
    TaskType,
    Text,
    WritingAssessment,
    criteria_for,
)

Identifier = Annotated[str, Field(strict=True, pattern=r"^[A-Za-z0-9_.:-]{1,100}$")]


class WritingSubmission(PublicModel):
    item_id: Text
    task_type: TaskType
    essay: Text


class ResolvedWritingTask(PublicModel):
    item_id: Text
    task_type: TaskType
    task_prompt: Text
    task_material_text: Text | None = None
    source: Literal["self_written", "llm_generated_verified", "open_license"]
    license: Text


class DescriptorChunk(PublicModel):
    chunk_id: Identifier
    test_part: TaskType
    criterion: Criterion
    band: Band
    version: Identifier
    source_url: Annotated[str, Field(pattern=r"^(https?://|mock://)[^\s]+$")]
    text: Text

    @model_validator(mode="after")
    def matching_criterion(self) -> Self:
        if self.criterion not in criteria_for(self.test_part):
            raise ValueError("descriptor criterion mismatches test_part")
        return self


class LLMGradingDraft(PublicModel):
    criteria: Annotated[list[CriterionAssessment], Field(min_length=4, max_length=4)]
    corrections: list[Correction]
    off_topic: StrictBool
    # --- Pedagogical feedback (optional — LLM may or may not produce these) ---
    top_priorities: list[ImprovementPriority] = []
    error_patterns: list[ErrorPattern] = []
    sentence_rewrites: list[SentenceRewrite] = []
    paragraph_analyses: list[ParagraphAnalysis] = []
    grammar_rules: list[GrammarRule] = []
    model_sentences: list[ModelSentence] = []


class PlagiarismMatch(PublicModel):
    source_id: Identifier
    evidence: Evidence


class PlagiarismResult(PublicModel):
    possible_plagiarism: StrictBool
    max_similarity: Annotated[float, Field(strict=True, ge=0, le=1, allow_inf_nan=False)]
    matches: list[PlagiarismMatch]


class SecurityResult(PublicModel):
    injection_detected: StrictBool


class IssueCode(StrEnum):
    SCHEMA_INVALID = "schema_invalid"
    EVIDENCE_MISSING = "evidence_missing"
    EVIDENCE_INVALID = "evidence_invalid"
    REFS_INVALID = "refs_invalid"
    CONSISTENCY_ERROR = "consistency_error"


class ValidationIssue(PublicModel):
    code: IssueCode
    criterion: Criterion | None = None


class ErrorCode(StrEnum):
    LLM_CONFIGURATION_ERROR = "LLM_CONFIGURATION_ERROR"
    LLM_AUTH_ERROR = "LLM_AUTH_ERROR"
    LLM_MODEL_UNAVAILABLE = "LLM_MODEL_UNAVAILABLE"
    LLM_RATE_LIMITED = "LLM_RATE_LIMITED"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_REQUEST_FAILED = "LLM_REQUEST_FAILED"
    LLM_RESPONSE_BLOCKED = "LLM_RESPONSE_BLOCKED"
    LLM_RESPONSE_INCOMPLETE = "LLM_RESPONSE_INCOMPLETE"
    LLM_EMPTY_RESPONSE = "LLM_EMPTY_RESPONSE"
    INVALID_INPUT = "INVALID_INPUT"
    UNKNOWN_ITEM = "UNKNOWN_ITEM"
    TASK_MISMATCH = "TASK_MISMATCH"
    INVALID_TASK = "INVALID_TASK"
    RETRIEVAL_INVALID = "RETRIEVAL_INVALID"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    ASSESSMENT_VALIDATION_FAILED = "ASSESSMENT_VALIDATION_FAILED"


class AgentSuccess(PublicModel):
    status: Literal["success"] = "success"
    run_id: Identifier
    assessment: WritingAssessment


ProviderCode = Literal[
    "json_validate_failed",
    "invalid_request_error",
    "invalid_api_key",
    "authentication_error",
    "permission_denied",
    "model_not_found",
    "rate_limit_exceeded",
    "rate_limit_error",
    "context_length_exceeded",
    "server_error",
    "service_unavailable",
    "insufficient_quota",
    "invalid_json_schema",
    "unsupported_value",
]


ProviderFailureKind = Literal["http", "connection", "timeout", "invalid_output", "unknown"]


class ProviderDiagnostics(PublicModel):
    """Allowlisted metadata only; no provider messages, response bodies or request payloads."""

    http_status: Annotated[int, Field(strict=True, ge=100, le=599)] | None = None
    provider_code: ProviderCode | None = None
    request_id: Annotated[str, Field(pattern=r"^req_[A-Za-z0-9-]{8,100}$")] | None = None
    retry_after_seconds: (
        Annotated[float, Field(strict=True, ge=0, le=86400, allow_inf_nan=False)] | None
    ) = None
    failure_kind: ProviderFailureKind


class AgentError(PublicModel):
    status: Literal["error"] = "error"
    run_id: Identifier
    code: ErrorCode
    retry_count: Annotated[int, Field(strict=True, ge=0, le=2)]
    errors: list[ValidationIssue]
    diagnostics: ProviderDiagnostics | None = None


class DraftGenerationFailure(Exception):
    """Provider explicitly reports invalid generated JSON; repair shares the graph budget."""

    def __init__(self, diagnostics: ProviderDiagnostics):
        self.diagnostics = diagnostics
        super().__init__(IssueCode.SCHEMA_INVALID.value)


class DependencyFailure(Exception):
    """Expected operational failure; exception messages never reach output or traces."""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.DEPENDENCY_UNAVAILABLE,
        *,
        diagnostics: ProviderDiagnostics | None = None,
    ):
        self.code = code
        self.diagnostics = diagnostics
        super().__init__(code.value)


class TaskBank(Protocol):
    def resolve(self, item_id: str) -> ResolvedWritingTask | None: ...


class Retriever(Protocol):
    def retrieve_descriptors(
        self, task_type: TaskType, criterion: Criterion, top_k: int = 3
    ) -> list[DescriptorChunk]: ...


class DeterministicTools(Protocol):
    def count_words(self, essay: str) -> int: ...
    def compute_band(self, bands: list[float]) -> float: ...
    def check_plagiarism(self, essay: str) -> PlagiarismResult: ...


class SecurityGuard(Protocol):
    def inspect(
        self,
        submission: WritingSubmission,
        task: ResolvedWritingTask,
        chunks: list[DescriptorChunk],
    ) -> SecurityResult: ...


class ExaminerInput(PublicModel):
    """All text fields are untrusted DATA; never system instructions or tool permissions."""

    submission: WritingSubmission
    task: ResolvedWritingTask
    chunks: list[DescriptorChunk]
    validation_errors: list[ValidationIssue]
    attempt: Annotated[int, Field(strict=True, ge=1, le=3)]


class ExaminerUsage(PublicModel):
    input_tokens: Annotated[int, Field(strict=True, ge=0)] | None = None
    output_tokens: Annotated[int, Field(strict=True, ge=0)] | None = None


@runtime_checkable
class UsageReportingExaminer(Protocol):
    @property
    def last_usage(self) -> ExaminerUsage | None: ...


class Examiner(Protocol):
    def generate(self, data: ExaminerInput) -> object: ...


class Validators(Protocol):
    def quote_validator(
        self, assessment: WritingAssessment, essay: str
    ) -> list[ValidationIssue]: ...
    def refs_validator(
        self, assessment: WritingAssessment, chunks: list[DescriptorChunk]
    ) -> list[ValidationIssue]: ...
    def consistency_validator(
        self,
        assessment: WritingAssessment,
        *,
        word_count: int,
        overall_band: float,
        plagiarism: PlagiarismResult,
        security: SecurityResult,
        off_topic: bool,
    ) -> list[ValidationIssue]: ...


@dataclass(frozen=True)
class Dependencies:
    task_bank: TaskBank
    retriever: Retriever
    tools: DeterministicTools
    examiner: Examiner
    validators: Validators
    security: SecurityGuard
    model_version: Identifier = "unspecified"
    prompt_version: Identifier = "unspecified"
