"""Shared skill entry point; checks delegate to injected N4 validators."""
from __future__ import annotations

from typing import Any, Protocol


class Validators(Protocol):
    def quote_validator(self, assessment: Any, essay: str) -> list[Any]: ...
    def refs_validator(self, assessment: Any, chunks: list[Any]) -> list[Any]: ...
    def consistency_validator(
        self, assessment: Any, *, word_count: int, overall_band: float,
        plagiarism: Any, security: Any, off_topic: bool,
    ) -> list[Any]: ...


def run_checks(
    assessment: Any,
    essay: str,
    chunks: list[Any],
    *,
    validators: Validators,
    word_count: int,
    overall_band: float,
    plagiarism: Any,
    security: Any,
    off_topic: bool,
) -> list[Any]:
    """Return N4 issues in stable order, separate from business flags."""
    issues = []
    issues.extend(validators.quote_validator(assessment, essay))
    issues.extend(validators.refs_validator(assessment, chunks))
    issues.extend(validators.consistency_validator(
        assessment, word_count=word_count, overall_band=overall_band,
        plagiarism=plagiarism, security=security, off_topic=off_topic,
    ))
    return issues
