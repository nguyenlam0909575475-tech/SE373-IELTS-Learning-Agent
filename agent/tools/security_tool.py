"""Flag explicit instruction attacks in untrusted text; never execute them.

This pattern guard is an additional signal. It is not a complete injection
defence and does not determine semantic relevance or adjust essay scores.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass

from .contracts import SecurityResult

_PATTERNS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    r"\b(?:ignore|disregard|override)\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|system|developer|above)\s+(?:\w+\s+){0,3}(?:instructions?|prompts?|rules?)\b",
    r"\b(?:reveal|print|show|leak|send)\b[^.!?\n]{0,70}\b(?:system\s+prompt|developer\s+(?:message|prompt)|api[ _-]?key|secret\s+key)\b",
    r"\b(?:examiner|grader|assistant)\s*[,;:]?\s*(?:please\s+)?(?:give|assign|award|set)\b[^.!?\n]{0,60}\b(?:band|score)\s*(?:to\s*)?9\b",
    r"\b(?:give|award|assign)\s+(?:me|this\s+(?:essay|response|answer))\b[^.!?\n]{0,40}\b(?:band|score)\s*9\b",
    r"<\|(?:im_start|start_header_id)\|>|\[/?INST\]|<\s*/?\s*(?:system|developer)\s*>",
    r"(?:bỏ\s+qua|phớt\s+lờ)\s+(?:mọi\s+)?(?:chỉ\s+dẫn|hướng\s+dẫn|lệnh)\s+(?:trước|hệ\s+thống)",
))


def _texts(record: object, depth: int = 0):
    if depth > 20:
        raise ValueError("untrusted input nesting exceeds the supported limit")
    if isinstance(record, str):
        yield record
    elif isinstance(record, Mapping):
        for key, item in record.items():
            yield from _texts(key, depth + 1)
            yield from _texts(item, depth + 1)
    elif isinstance(record, (list, tuple)):
        for item in record:
            yield from _texts(item, depth + 1)
    elif is_dataclass(record) and not isinstance(record, type):
        yield from _texts(asdict(record), depth + 1)
    elif callable(getattr(record, "model_dump", None)):
        yield from _texts(record.model_dump(mode="python"), depth + 1)
    elif hasattr(record, "__dict__"):
        yield from _texts(vars(record), depth + 1)


class SecurityGuard:
    def inspect(self, submission: object, task: object, chunks: list) -> SecurityResult:
        detected = any(
            pattern.search(text)
            for record in (submission, task, chunks)
            for text in _texts(record)
            for pattern in _PATTERNS
        )
        return SecurityResult(detected)
