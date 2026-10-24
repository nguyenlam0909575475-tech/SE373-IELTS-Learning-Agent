"""Delegate skill checks to the supplied Member 4 validators; no scoring logic."""
from typing import Protocol, Any


class Validators(Protocol):
    def quote_validator(self, assessment, essay: str) -> list: ...
    def refs_validator(self, assessment, chunks: list) -> list: ...
    def consistency_validator(self, assessment, *, word_count, overall_band,
                              plagiarism, security, off_topic) -> list: ...


def run_checks(assessment: Any, essay: str, chunks: list, *, validators: Validators,
               word_count: int, overall_band: float, plagiarism: Any,
               security: Any, off_topic: bool) -> list:
    """Run after Member 3 Pydantic validation, using independent tool results.

    Preserve Member 4 issue objects. Operational errors propagate to the graph;
    an unavailable validator must never look like an empty/successful result.
    """
    issues = []
    for result in (
        validators.quote_validator(assessment, essay),
        validators.refs_validator(assessment, chunks),
        validators.consistency_validator(
            assessment, word_count=word_count, overall_band=overall_band,
            plagiarism=plagiarism, security=security, off_topic=off_topic,
        ),
    ):
        if not isinstance(result, list):
            raise TypeError("Member 4 validators must return list[ValidationIssue]")
        issues.extend(result)
    return issues
