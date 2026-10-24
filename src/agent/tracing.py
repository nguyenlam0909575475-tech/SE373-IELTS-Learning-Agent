"""Allowlisted trace DTOs only: never serialize state, inputs or exception messages."""

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Callable, TypedDict, TypeVar

from pydantic import Field, ValidationError

from .contracts import (
    DependencyFailure,
    DraftGenerationFailure,
    ErrorCode,
    Identifier,
    IssueCode,
    ProviderDiagnostics,
)
from .schemas import PublicModel

T = TypeVar("T")


class TraceContext(TypedDict):
    run_id: str
    attempt: int
    retrieved_chunk_ids: list[str]
    descriptor_versions: list[str]
    model_version: str
    prompt_version: str
    skill_name: str
    skill_version: str


class TraceEvent(PublicModel):
    run_id: Identifier
    node: Identifier
    kind: str = "node"
    started_at: str
    ended_at: str
    duration_ms: float = Field(ge=0)
    attempt: int
    codes: list[ErrorCode | IssueCode]
    retrieved_chunk_ids: list[Identifier]
    descriptor_versions: list[Identifier]
    model_version: Identifier
    prompt_version: Identifier
    skill_name: Identifier
    skill_version: Identifier
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: None = None
    provider_diagnostics: ProviderDiagnostics | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def timed_call(
    name: str, call: Callable[[], T], events: list[TraceEvent], context: TraceContext
) -> T:
    start, clock = utc_now(), perf_counter()
    codes: list[ErrorCode | IssueCode] = []
    diagnostics: ProviderDiagnostics | None = None
    try:
        return call()
    except DraftGenerationFailure as exc:
        diagnostics = exc.diagnostics
        codes = [IssueCode.SCHEMA_INVALID]
        raise
    except ValidationError:
        codes = [
            IssueCode.SCHEMA_INVALID
            if name == "examiner_generate"
            else ErrorCode.DEPENDENCY_UNAVAILABLE
        ]
        raise
    except Exception as exc:
        if isinstance(exc, DependencyFailure):
            diagnostics = exc.diagnostics
        codes = [
            exc.code if isinstance(exc, DependencyFailure) else ErrorCode.DEPENDENCY_UNAVAILABLE
        ]
        raise
    finally:
        events.append(
            TraceEvent(
                **context,
                node=name,
                kind="tool",
                started_at=start,
                ended_at=utc_now(),
                duration_ms=(perf_counter() - clock) * 1000,
                codes=codes,
                provider_diagnostics=diagnostics,
            )
        )


def write_jsonl(path: Path, events: list[TraceEvent]) -> None:
    """Explicit opt-in export, normally synthetic demo only; no global logger/sink."""
    with path.open("w", encoding="utf-8") as file:
        for event in events:
            file.write(event.model_dump_json() + "\n")
