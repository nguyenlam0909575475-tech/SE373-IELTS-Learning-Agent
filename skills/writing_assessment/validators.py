from __future__ import annotations

import re
from math import isclose

from agent.tools.compute_tool import compute_band
from agent.tools.contracts import ShapeError, ValidationIssue, is_band, read_field, value

COMMON_CRITERIA = {"coherence_and_cohesion", "lexical_resource", "grammatical_range_and_accuracy"}
_CRITERION_ALIASES = {
    "coherence_cohesion": "coherence_and_cohesion",
    "grammatical_range_accuracy": "grammatical_range_and_accuracy",
}


def criterion_name(item: object):
    name = value(read_field(item, "criterion"))
    return _CRITERION_ALIASES.get(name, name) if isinstance(name, str) else name

def criteria_for(assessment: object) -> tuple[str, list]:
    task = value(read_field(assessment, "task_type"))
    if task not in ("task1", "task2"):
        raise ShapeError("task_type is invalid")
    criteria = read_field(assessment, "criteria")
    if not isinstance(criteria, list) or len(criteria) != 4:
        raise ShapeError("four criteria are required")
    names = [criterion_name(item) for item in criteria]
    first = "task_achievement" if task == "task1" else "task_response"
    if any(not isinstance(name, str) for name in names) or set(names) != COMMON_CRITERIA | {first}:
        raise ShapeError("criterion set is invalid")
    return task, criteria

def format_issue(issue: ValidationIssue) -> str:
    """Keep machine code, location and reason without echoing student text."""
    location = issue.path or issue.criterion or "assessment"
    return f"{issue.code} at {location}: {issue.reason or 'validation failed'}"


def quote_validator(assessment: object, essay: str) -> list[ValidationIssue]:
    if not isinstance(essay, str):
        raise TypeError("essay must be a string")
    try:
        _, criteria = criteria_for(assessment)
    except ShapeError:
        return [ValidationIssue("schema_invalid")]
    issues = []
    for ci, item in enumerate(criteria):
        name = criterion_name(item)
        base = f"criteria[{ci}].evidence"
        try:
            evidence = read_field(item, "evidence")
        except ShapeError:
            evidence = None
        if evidence is None or evidence == []:
            issues.append(ValidationIssue("evidence_missing", name, "evidence is required", base))
            continue
        if not isinstance(evidence, list):
            issues.append(ValidationIssue("evidence_invalid", name, "evidence must be a list", base))
            continue
        for ei, span in enumerate(evidence):
            reason = ""
            try:
                quote = read_field(span, "quote")
                start = read_field(span, "start_char")
                end = read_field(span, "end_char")
                if not isinstance(quote, str) or not quote.strip():
                    reason = "quote must contain text"
                elif quote not in essay:
                    reason = "quote not found verbatim in essay"
                elif (type(start) is not int or type(end) is not int
                      or not 0 <= start < end <= len(essay) or essay[start:end] != quote):
                    reason = "char offset does not match the quote"
            except ShapeError:
                reason = "quote or char offset fields are missing"
            if reason:
                issues.append(ValidationIssue("evidence_invalid", name, reason, f"{base}[{ei}]"))
    # New PR22 feedback also claims to quote the submission. Validate those
    # claims before displaying advice, just like criterion evidence.
    for collection, field in (("top_priorities", "example_quote"), ("sentence_rewrites", "original_sentence")):
        try:
            rows = read_field(assessment, collection)
        except ShapeError:
            continue  # Legacy assessments do not contain these optional fields.
        if not isinstance(rows, list):
            issues.append(ValidationIssue("evidence_invalid", path=collection))
            continue
        for index, row in enumerate(rows):
            try:
                quote = read_field(row, field)
                valid = isinstance(quote, str) and bool(quote.strip()) and quote in essay
            except ShapeError:
                valid = False
            if not valid:
                issues.append(ValidationIssue(
                    "evidence_invalid", reason="feedback quote not found verbatim in essay",
                    path=f"{collection}[{index}].{field}",
                ))
    return issues

_ID = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z")

def refs_validator(assessment: object, chunks: list) -> list[ValidationIssue]:
    try:
        task, criteria = criteria_for(assessment)
    except ShapeError:
        return [ValidationIssue("schema_invalid")]
    try:
        if not isinstance(chunks, list) or not chunks:
            raise ShapeError("retrieval is empty")
        lookup = {}
        allowed = COMMON_CRITERIA | {"task_achievement" if task == "task1" else "task_response"}
        for chunk in chunks:
            chunk_id = read_field(chunk, "chunk_id")
            version = read_field(chunk, "version")
            criterion = criterion_name(chunk)
            if (
                not isinstance(chunk_id, str) or not _ID.fullmatch(chunk_id)
                or chunk_id in lookup
                or value(read_field(chunk, "test_part")) != task
                or not isinstance(criterion, str) or criterion not in allowed
                or not is_band(read_field(chunk, "band"))
                or not isinstance(version, str) or not _ID.fullmatch(version)
                or any(not isinstance(read_field(chunk, key), str) or not read_field(chunk, key).strip()
                       for key in ("source_url", "text"))
            ):
                raise ShapeError("retrieval metadata is invalid")
            lookup[chunk_id] = criterion
    except ShapeError:
        return [ValidationIssue("refs_invalid", reason="retrieved chunks are empty or have invalid metadata", path="retrieved_descriptors")]
    issues = []
    for item in criteria:
        name = criterion_name(item)
        try:
            refs = read_field(item, "descriptor_refs")
            valid = (
                isinstance(refs, list) and bool(refs)
                and all(isinstance(ref, str) for ref in refs)
                and len(set(refs)) == len(refs)
                and all(lookup.get(ref) == name for ref in refs)
            )
        except ShapeError:
            valid = False
        if not valid:
            issues.append(ValidationIssue("refs_invalid", name, "refs must be unique retrieved IDs for the same criterion", f"{name}.descriptor_refs"))
    return issues

def consistency_validator(
    assessment: object, *, word_count: int, overall_band: float | None = None,
    plagiarism: object | None = None, security: object | None = None, off_topic: bool | None = None,
) -> list[ValidationIssue]:
    """Compare output with code results and any supplied trusted signals.

    None means not checked, never a trusted negative. Off-topic detection is
    external; this validator only checks the flag and the required score cap.
    """
    try:
        task, criteria = criteria_for(assessment)
        bands = [read_field(item, "band") for item in criteria]
        count = read_field(assessment, "word_count")
        total = read_field(assessment, "overall_band")
        flags = read_field(assessment, "flags")
        if (
            type(count) is not int or count < 0 or type(word_count) is not int or word_count < 0
            or not all(is_band(band) for band in bands) or not is_band(total)
            or (overall_band is not None and not is_band(overall_band))
            or not isinstance(flags, list)
            or any(not isinstance(value(flag), str) for flag in flags)
        ):
            raise ShapeError("invalid field type or range")
        signals = {"under_length": word_count < (150 if task == "task1" else 250)}
        for flag, result, field in (
            ("possible_plagiarism", plagiarism, "possible_plagiarism"),
            ("injection_detected", security, "injection_detected"),
        ):
            if result is not None:
                signals[flag] = read_field(result, field)
        if off_topic is not None:
            signals["off_topic"] = off_topic
        if any(type(present) is not bool for present in signals.values()):
            raise ShapeError("trusted signals must be booleans")
        flag_values = [value(flag) for flag in flags]
        allowed = {"under_length", "off_topic", "possible_plagiarism", "injection_detected"}
        reasons = []
        if count != word_count:
            reasons.append("word_count differs from the tool result")
        if not isclose(total, compute_band(bands), rel_tol=0, abs_tol=1e-9):
            reasons.append("overall_band differs from compute_band")
        if overall_band is not None and not isclose(total, overall_band, rel_tol=0, abs_tol=1e-9):
            reasons.append("overall_band differs from the supplied code result")
        if len(flag_values) != len(set(flag_values)) or not set(flag_values) <= allowed:
            reasons.append("flags contain duplicates or unknown values")
        for flag, present in signals.items():
            if (flag in flag_values) != present:
                reasons.append(f"flag {flag} differs from the trusted result")
        first = "task_achievement" if task == "task1" else "task_response"
        if off_topic is True or "off_topic" in flag_values:
            first_band = next(read_field(item, "band") for item in criteria
                              if value(read_field(item, "criterion")) == first)
            if first_band > 5:
                reasons.append(f"off_topic requires {first} <= 5.0")
    except ShapeError:
        return [ValidationIssue("schema_invalid", reason="invalid field type or range")]
    return [ValidationIssue("consistency_error", reason=reason) for reason in reasons]
