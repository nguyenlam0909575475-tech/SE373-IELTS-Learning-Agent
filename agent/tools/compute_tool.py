"""Deterministic word count and one-Task band calculation."""

from __future__ import annotations

import re
from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal
from math import isfinite

WORD_PATTERN = r"\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b"
_WORD_REGEX = re.compile(WORD_PATTERN)


def count_words(essay: str) -> int:
    """Return the number of matches of WORD_PATTERN in the original text.

    Straight apostrophes and hyphens join word parts: "don't" and
    "state-of-the-art" each count as one word. No text normalization is
    applied, so the result follows the shared regex exactly.

    Raises:
        TypeError: If essay is not a string.
    """
    if not isinstance(essay, str):
        raise TypeError("text must be a string")

    return len(_WORD_REGEX.findall(essay))


def compute_band(bands: Sequence[int | float]) -> float:
    """Calculate the Task band using the current repository rounding policy.

    Matches the existing N3 checks: 6.25 becomes 6.5; 6.75 becomes 7.0.
    This calculates one Task's band, not a combined exam score.
    Each input must be a finite int or float between 0 and 9 inclusive.
    Decimal arithmetic preserves the decimal inputs before conversion to float.

    Raises:
        TypeError: If scores is not a sequence of numbers, or contains bools.
        ValueError: If there are not exactly four scores, or a score is
            non-finite or outside the range [0, 9].
    """
    if not isinstance(bands, Sequence) or isinstance(bands, (str, bytes)):
        raise TypeError("scores must be a sequence of four numbers")
    if len(bands) != 4:
        raise ValueError("exactly four criterion scores are required")

    decimal_scores = []
    for index, score in enumerate(bands):
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise TypeError(f"scores[{index}] must be an int or float")
        if isinstance(score, float) and not isfinite(score):
            raise ValueError(f"scores[{index}] must be finite")
        if not 0 <= score <= 9:
            raise ValueError(f"scores[{index}] must be between 0 and 9")
        decimal_scores.append(Decimal(str(score)))

    average = sum(decimal_scores, Decimal(0)) / Decimal(4)
    return float((average * 2).quantize(Decimal(1), rounding=ROUND_HALF_UP) / 2)

compute_task_band = compute_band
