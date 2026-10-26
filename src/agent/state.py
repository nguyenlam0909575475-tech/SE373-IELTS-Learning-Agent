"""Per-invoke private state; only result/trace are exposed by compiled graph output."""

from typing import TypedDict

from .contracts import (
    AgentError,
    AgentSuccess,
    DescriptorChunk,
    ErrorCode,
    LLMGradingDraft,
    PlagiarismResult,
    ProviderDiagnostics,
    ResolvedWritingTask,
    SecurityResult,
    ValidationIssue,
    WritingSubmission,
)
from .schemas import WritingAssessment
from .tracing import TraceEvent


class GraphInput(TypedDict):
    request: object


class GraphOutput(TypedDict):
    result: AgentSuccess | AgentError
    trace: list[TraceEvent]


class AgentState(TypedDict, total=False):
    request: object
    submission: WritingSubmission
    resolved_task: ResolvedWritingTask
    retrieved_chunks: list[DescriptorChunk]
    word_count: int
    plagiarism_result: PlagiarismResult
    security_result: SecurityResult
    grading_draft: LLMGradingDraft | None
    validation_errors: list[ValidationIssue]
    attempt_count: int
    run_id: str
    candidate: WritingAssessment | None
    error_code: ErrorCode | None
    diagnostics: ProviderDiagnostics | None
    result: AgentSuccess | AgentError
    trace: list[TraceEvent]
