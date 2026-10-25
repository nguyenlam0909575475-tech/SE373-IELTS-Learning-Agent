"""Injected node implementations. Operational failures stop; draft issues may repair."""

from collections.abc import Callable
from time import perf_counter
from typing import Any, Protocol
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from src.skill_checks import run_checks

from .contracts import (
    AgentError,
    AgentSuccess,
    Dependencies,
    DependencyFailure,
    DescriptorChunk,
    DraftGenerationFailure,
    ErrorCode,
    ExaminerInput,
    IssueCode,
    LLMGradingDraft,
    PlagiarismResult,
    ResolvedWritingTask,
    SecurityResult,
    UsageReportingExaminer,
    ValidationIssue,
    WritingSubmission,
)
from .prompts import SKILL_NAME, SKILL_VERSION
from .schemas import DISCLAIMER, Band, Evidence, Flag, WritingAssessment, criteria_for
from .state import AgentState
from .tracing import TraceContext, TraceEvent, timed_call, utc_now

MAX_ATTEMPTS = 3


class NodeCallable(Protocol):
    def __call__(self, state: AgentState) -> dict[str, Any]: ...


class Nodes:
    def __init__(self, dependencies: Dependencies):
        self.deps = dependencies

    def wrap(self, name: str) -> NodeCallable:
        action = getattr(self, name)

        def run(state: AgentState) -> dict[str, Any]:
            base: AgentState = {}
            if name == "resolve_task":
                base = dict(
                    run_id=str(uuid4()),
                    attempt_count=0,
                    validation_errors=[],
                    retrieved_chunks=[],
                    trace=[],
                    error_code=None,
                    candidate=None,
                    grading_draft=None,
                    diagnostics=None,
                )
                state = {**state, **base}
            if name == "examiner":
                base["attempt_count"] = state["attempt_count"] + 1
                state = {**state, **base}
            start, clock = utc_now(), perf_counter()
            events: list[TraceEvent] = []
            context: TraceContext = dict(
                run_id=state["run_id"],
                attempt=state["attempt_count"],
                retrieved_chunk_ids=[],
                descriptor_versions=[],
                model_version=self.deps.model_version,
                prompt_version=self.deps.prompt_version,
                skill_name=SKILL_NAME,
                skill_version=SKILL_VERSION,
            )

            def call(tool: str, fn: Callable) -> Any:
                try:
                    return timed_call(tool, fn, events, context)
                finally:
                    if tool == "examiner_generate" and isinstance(
                        self.deps.examiner, UsageReportingExaminer
                    ):
                        usage = self.deps.examiner.last_usage
                        if usage is not None:
                            events[-1].input_tokens = usage.input_tokens
                            events[-1].output_tokens = usage.output_tokens

            try:
                update = action(state, call)
            except DependencyFailure as exc:
                update = {"error_code": exc.code, "diagnostics": exc.diagnostics}
            except Exception:
                # Integration boundary: do not leak messages, raw Pydantic input or partial grades.
                update = {"error_code": ErrorCode.DEPENDENCY_UNAVAILABLE}
            merged = {**state, **update}
            chunks = merged.get("retrieved_chunks", [])
            ids = [c.chunk_id for c in chunks]
            versions = sorted({c.version for c in chunks})
            codes = [e.code for e in merged.get("validation_errors", [])]
            if merged.get("error_code"):
                codes.append(merged["error_code"])
            context["retrieved_chunk_ids"] = ids
            context["descriptor_versions"] = versions
            for event in events:
                event.retrieved_chunk_ids = ids
                event.descriptor_versions = versions
            events.append(
                TraceEvent(
                    **context,
                    node=name,
                    started_at=start,
                    ended_at=utc_now(),
                    duration_ms=(perf_counter() - clock) * 1000,
                    codes=codes,
                    provider_diagnostics=merged.get("diagnostics"),
                )
            )
            return {**base, **update, "trace": state.get("trace", []) + events}

        return run

    def resolve_task(self, state: AgentState, call: Callable) -> dict[str, Any]:
        try:
            request = WritingSubmission.model_validate(state.get("request"))
        except ValidationError:
            return {"error_code": ErrorCode.INVALID_INPUT}
        raw = call("resolve_item", lambda: self.deps.task_bank.resolve(request.item_id))
        if raw is None:
            return {"error_code": ErrorCode.UNKNOWN_ITEM}
        try:
            task = ResolvedWritingTask.model_validate(raw)
        except ValidationError:
            return {"error_code": ErrorCode.INVALID_TASK}
        if task.item_id != request.item_id:
            return {"error_code": ErrorCode.INVALID_TASK}
        if task.task_type != request.task_type:
            return {"error_code": ErrorCode.TASK_MISMATCH}
        if task.task_type.value == "task1" and not task.task_material_text:
            return {"error_code": ErrorCode.INVALID_TASK}
        return {"submission": request, "resolved_task": task}

    def prepare_tools(self, state: AgentState, call: Callable) -> dict[str, Any]:
        essay = state["submission"].essay
        count = call("count_words", lambda: self.deps.tools.count_words(essay))
        if type(count) is not int or count < 0:
            raise DependencyFailure()
        plagiarism = PlagiarismResult.model_validate(
            call("check_plagiarism", lambda: self.deps.tools.check_plagiarism(essay))
        )
        return {"word_count": count, "plagiarism_result": plagiarism}

    def retrieve_rubric(self, state: AgentState, call: Callable) -> dict[str, Any]:
        task = state["submission"].task_type
        chunks: list[DescriptorChunk] = []
        seen = set()
        for criterion in criteria_for(task):
            raw = call(
                "retrieve_descriptors",
                lambda crit=criterion: self.deps.retriever.retrieve_descriptors(task, crit, top_k=3),
            )
            try:
                batch = TypeAdapter(list[DescriptorChunk]).validate_python(raw, strict=True)
            except ValidationError:
                return {"error_code": ErrorCode.RETRIEVAL_INVALID}
            if not 1 <= len(batch) <= 3:
                return {"error_code": ErrorCode.RETRIEVAL_INVALID}
            for chunk in batch:
                if (
                    chunk.test_part != task
                    or chunk.criterion != criterion
                    or chunk.chunk_id in seen
                ):
                    return {"error_code": ErrorCode.RETRIEVAL_INVALID}
                seen.add(chunk.chunk_id)
                chunks.append(chunk)
        security = SecurityResult.model_validate(
            call(
                "security_inspect",
                lambda: self.deps.security.inspect(
                    state["submission"], state["resolved_task"], chunks
                ),
            )
        )
        return {"retrieved_chunks": chunks, "security_result": security}

    def examiner(self, state: AgentState, call: Callable) -> dict[str, Any]:
        data = ExaminerInput(
            submission=state["submission"],
            task=state["resolved_task"],
            chunks=state["retrieved_chunks"],
            validation_errors=state["validation_errors"],
            attempt=state["attempt_count"],
        )
        try:
            raw = call("examiner_generate", lambda: self.deps.examiner.generate(data))
            draft = LLMGradingDraft.model_validate(raw)
        except DraftGenerationFailure as exc:
            return {
                "grading_draft": None,
                "candidate": None,
                "diagnostics": exc.diagnostics,
                "validation_errors": [ValidationIssue(code=IssueCode.SCHEMA_INVALID)],
            }
        except ValidationError:
            return {
                "diagnostics": None,
                "grading_draft": None,
                "candidate": None,
                "validation_errors": [ValidationIssue(code=IssueCode.SCHEMA_INVALID)],
            }
        return {
            "grading_draft": draft,
            "candidate": None,
            "validation_errors": [],
            "diagnostics": None,
        }

    def verify(self, state: AgentState, call: Callable) -> dict[str, Any]:
        draft = state["grading_draft"]
        if draft is None:
            return {}
        overall = TypeAdapter(Band).validate_python(
            call(
                "compute_band",
                lambda: self.deps.tools.compute_band([c.band for c in draft.criteria]),
            )
        )
        request = state["submission"]
        flags = []
        threshold = 150 if request.task_type.value == "task1" else 250
        if state["word_count"] < threshold:
            flags.append(Flag.UNDER_LENGTH)
        if draft.off_topic:
            flags.append(Flag.OFF_TOPIC)
        if state["plagiarism_result"].possible_plagiarism:
            flags.append(Flag.POSSIBLE_PLAGIARISM)
        if state["security_result"].injection_detected:
            flags.append(Flag.INJECTION_DETECTED)
        for c in draft.criteria:
            for i, ev in enumerate(c.evidence):
                if ev.quote in request.essay and (
                    ev.end_char > len(request.essay)
                    or request.essay[ev.start_char : ev.end_char] != ev.quote
                ):
                    idx = request.essay.find(ev.quote)
                    if idx != -1:
                        c.evidence[i] = Evidence(
                            quote=ev.quote, start_char=idx, end_char=idx + len(ev.quote)
                        )
        try:
            assessment = WritingAssessment(
                task_type=request.task_type,
                word_count=state["word_count"],
                criteria=draft.criteria,
                overall_band=overall,
                corrections=draft.corrections,
                flags=flags,
                disclaimer=DISCLAIMER,
            )
        except ValidationError:
            return {"validation_errors": [ValidationIssue(code=IssueCode.SCHEMA_INVALID)]}
        issues = call(
            "writing_skill_checks",
            lambda: run_checks(
                assessment,
                request.essay,
                state["retrieved_chunks"],
                validators=self.deps.validators,
                word_count=state["word_count"],
                overall_band=overall,
                plagiarism=state["plagiarism_result"],
                security=state["security_result"],
                off_topic=draft.off_topic,
            ),
        )
        validated = TypeAdapter(list[ValidationIssue]).validate_python(issues, strict=True)
        return {"validation_errors": validated, "candidate": assessment if not validated else None}

    def finalize(self, state: AgentState, call: Callable) -> dict[str, Any]:
        candidate = state.get("candidate")
        if candidate is None or state["validation_errors"] or state.get("error_code"):
            raise DependencyFailure()
        return {"result": AgentSuccess(run_id=state["run_id"], assessment=candidate)}

    def failure(self, state: AgentState, call: Callable) -> dict[str, Any]:
        return {
            "result": AgentError(
                run_id=state["run_id"],
                code=state.get("error_code") or ErrorCode.ASSESSMENT_VALIDATION_FAILED,
                retry_count=max(0, state["attempt_count"] - 1),
                errors=state["validation_errors"],
                diagnostics=state.get("diagnostics"),
            )
        }
