"""Small transport records for N4, shared with the existing WritingAssessment schema.

Inputs can be mappings or schema objects. The authoritative assessment schema stays in skills.writing_assessment.checks.
No record/error here contains the full submission or credentials.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite


@dataclass(frozen=True)
class Evidence:
    quote: str
    start_char: int
    end_char: int


@dataclass(frozen=True)
class PlagiarismMatch:
    source_id: str
    evidence: Evidence


@dataclass(frozen=True)
class PlagiarismResult:
    possible_plagiarism: bool
    max_similarity: float
    matches: list[PlagiarismMatch] = field(default_factory=list)


@dataclass(frozen=True)
class SecurityResult:
    injection_detected: bool


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    criterion: str | None = None
    reason: str = ""
    path: str = ""


class Member4DependencyError(RuntimeError):
    """Sanitized dependency failure; the caller must stop or request the missing data."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class ShapeError(ValueError):
    """An input is missing a field consumed by a deterministic check."""


def read_field(record: object, name: str):
    try:
        return record[name] if isinstance(record, Mapping) else getattr(record, name)
    except (KeyError, AttributeError, TypeError):
        raise ShapeError("required field is missing") from None


def value(item: object):
    return item.value if isinstance(item, Enum) else item


def is_band(item: object) -> bool:
    return (
        not isinstance(item, bool)
        and isinstance(item, (int, float))
        and 0 <= item <= 9
        and isfinite(item)
    )
